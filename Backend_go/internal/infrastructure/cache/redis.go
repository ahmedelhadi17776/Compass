package cache

import (
    "context"
    "encoding/json"
    "fmt"
    "time"
    "compress/gzip"
    "strings"
    "bytes"
    "io"

    "github.com/go-redis/redis/v8"
    "github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
    "go.uber.org/zap"
)

var log = logger.NewLogger()

// CacheMetrics tracks cache hit/miss statistics
type CacheMetrics struct {
    Hits      int64
    Misses    int64
    HitRate   float64
    LastReset int64
    ByType    map[string]TypeMetrics
}

// TypeMetrics tracks metrics for a specific cache type
type TypeMetrics struct {
    Hits   int64
    Misses int64
}

// RedisClient wraps the Redis client with additional functionality
type RedisClient struct {
    client  *redis.Client
    metrics CacheMetrics
    ttls    map[string]int
    contextTimeout time.Duration
    useCompression bool
}

const (
    ErrCacheNotFound   = "cache: key not found"
    ErrCacheConnection = "cache: connection error"
    ErrCacheTimeout    = "cache: operation timeout"
)

// NewRedisClient creates a new Redis client
func NewRedisClient(addr, password string, db int) (*RedisClient, error) {
    client := redis.NewClient(&redis.Options{
        Addr:         addr,
        Password:     password,
        DB:           db,
        PoolSize:     100,
        MinIdleConns: 10,
        MaxRetries:   3,
    })

    // Test connection
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    if _, err := client.Ping(ctx).Result(); err != nil {
        return nil, fmt.Errorf("failed to connect to Redis: %w", err)
    }

    return &RedisClient{
        client: client,
        metrics: CacheMetrics{
            LastReset: time.Now().Unix(),
            ByType:    make(map[string]TypeMetrics),
        },
        ttls: map[string]int{
            "default":    1800,  // 30 minutes
            "task":       3600,  // 1 hour
            "user":       7200,  // 2 hours
            "project":    3600,  // 1 hour
            "workflow":   3600,  // 1 hour
            "event":      1800,  // 30 minutes
            "task_list":  600,   // 10 minutes
            "event_list": 600,   // 10 minutes
        },
        contextTimeout: 5 * time.Second,
    }, nil
}

// Get retrieves a value from the cache
func (r *RedisClient) Get(ctx context.Context, key string) (string, error) {
    val, err := r.client.Get(ctx, key).Result()
    if err != nil {
        if err == redis.Nil {
            return "", fmt.Errorf("%s: %s", ErrCacheNotFound, key)
        }
        return "", fmt.Errorf("%s: %w", ErrCacheConnection, err)
    }
    return val, nil
}

// Set stores a value in the cache with the specified TTL
func (r *RedisClient) Set(ctx context.Context, key, value string, ttl time.Duration) error {
    return r.client.Set(ctx, key, value, ttl).Err()
}

// Delete removes a value from the cache
func (r *RedisClient) Delete(ctx context.Context, keys ...string) error {
    return r.client.Del(ctx, keys...).Err()
}

// GenerateCacheKey creates a unique cache key for the given entity
func GenerateCacheKey(entityType string, entityID interface{}, action string) string {
    if action == "" {
        return fmt.Sprintf("%s:%v", entityType, entityID)
    }
    return fmt.Sprintf("%s:%v:%s", entityType, entityID, action)
}

// CacheResponse is a generic function to cache any serializable response
func (r *RedisClient) CacheResponse(ctx context.Context, key string, ttl time.Duration, cacheType string, fn func() (interface{}, error)) (interface{}, error) {
    // Try to get from cache first
    cachedData, err := r.Get(ctx, key)
    if err != nil {
        log.Error("Error getting from cache", zap.Error(err))
    } else if cachedData != "" {
        // Track cache hit
        r.trackCacheEvent(true, cacheType)
        log.Debug("Cache hit", zap.String("key", key), zap.String("type", cacheType))
        
        // Deserialize the cached data
        var result interface{}
        if err := json.Unmarshal([]byte(cachedData), &result); err != nil {
            log.Error("Error deserializing cached data", zap.Error(err))
        } else {
            return result, nil
        }
    }

    // Cache miss, execute the function
    r.trackCacheEvent(false, cacheType)
    log.Debug("Cache miss", zap.String("key", key), zap.String("type", cacheType))
    
    result, err := fn()
    if err != nil {
        return nil, err
    }

    // Don't cache nil results
    if result == nil {
        return nil, nil
    }

    // Serialize and cache the result
    data, err := json.Marshal(result)
    if err != nil {
        log.Error("Error serializing result", zap.Error(err))
        return result, nil
    }

    if err := r.Set(ctx, key, string(data), ttl); err != nil {
        log.Error("Error caching result", zap.Error(err))
    }

    return result, nil
}

// InvalidateCache removes all cache entries for a specific entity
func (r *RedisClient) InvalidateCache(ctx context.Context, entityType string, entityID interface{}) error {
    pattern := fmt.Sprintf("%s:%v*", entityType, entityID)
    return r.ClearByPattern(ctx, pattern)
}

// ClearByPattern removes all cache entries matching the given pattern
func (r *RedisClient) ClearByPattern(ctx context.Context, pattern string) error {
    iter := r.client.Scan(ctx, 0, pattern, 100).Iterator()
    var keys []string

    for iter.Next(ctx) {
        keys = append(keys, iter.Val())
    }

    if err := iter.Err(); err != nil {
        return err
    }

    if len(keys) > 0 {
        return r.Delete(ctx, keys...)
    }

    return nil
}

// GetCacheStats returns cache statistics
func (r *RedisClient) GetCacheStats(ctx context.Context) (map[string]interface{}, error) {
    _, err := r.client.Info(ctx, "stats").Result()
    if err != nil {
        return nil, err
    }

    // Parse Redis info
    redisHitRate := 0.0
    // In a real implementation, parse the info string to extract hit rate

    // Calculate application hit rate
    appHitRate := float64(r.metrics.Hits) / float64(r.metrics.Hits+r.metrics.Misses)
    if r.metrics.Hits+r.metrics.Misses == 0 {
        appHitRate = 0
    }

    // Prepare type metrics
    typeMetrics := make(map[string]map[string]interface{})
    for cacheType, metrics := range r.metrics.ByType {
        typeHitRate := float64(metrics.Hits) / float64(metrics.Hits+metrics.Misses)
        if metrics.Hits+metrics.Misses == 0 {
            typeHitRate = 0
        }

        typeMetrics[cacheType] = map[string]interface{}{
            "hits":     metrics.Hits,
            "misses":   metrics.Misses,
            "hit_rate": typeHitRate,
        }
    }

    return map[string]interface{}{
        "redis": map[string]interface{}{
            "hit_rate":   redisHitRate,
            "total_keys": r.client.DBSize(ctx).Val(),
        },
        "app": map[string]interface{}{
            "hits":          r.metrics.Hits,
            "misses":        r.metrics.Misses,
            "hit_rate":      appHitRate,
            "tracking_since": time.Unix(r.metrics.LastReset, 0).Format(time.RFC3339),
            "by_type":       typeMetrics,
        },
    }, nil
}

// ResetCacheMetrics resets the cache hit/miss metrics
func (r *RedisClient) ResetCacheMetrics() {
    r.metrics = CacheMetrics{
        Hits:      0,
        Misses:    0,
        HitRate:   0,
        LastReset: time.Now().Unix(),
        ByType:    make(map[string]TypeMetrics),
    }
}

// trackCacheEvent tracks a cache hit or miss event
func (r *RedisClient) trackCacheEvent(hit bool, cacheType string) {
    if hit {
        r.metrics.Hits++
    } else {
        r.metrics.Misses++
    }

    // Update hit rate
    total := r.metrics.Hits + r.metrics.Misses
    if total > 0 {
        r.metrics.HitRate = float64(r.metrics.Hits) / float64(total)
    }

    // Initialize cache type if not exists
    if _, ok := r.metrics.ByType[cacheType]; !ok {
        r.metrics.ByType[cacheType] = TypeMetrics{}
    }

    // Update type metrics
    typeMetrics := r.metrics.ByType[cacheType]
    if hit {
        typeMetrics.Hits++
    } else {
        typeMetrics.Misses++
    }
    r.metrics.ByType[cacheType] = typeMetrics
}

func (r *RedisClient) Close() error {
    return r.client.Close()
}

func (r *RedisClient) HealthCheck(ctx context.Context) error {
    status := r.client.Ping(ctx)
    return status.Err()
}

func (r *RedisClient) MGet(ctx context.Context, keys []string) ([]string, error) {
    results, err := r.client.MGet(ctx, keys...).Result()
    if err != nil {
        return nil, err
    }
    
    strings := make([]string, len(results))
    for i, result := range results {
        if result != nil {
            strings[i] = result.(string)
        }
    }
    return strings, nil
}

func (r *RedisClient) MSet(ctx context.Context, values map[string]string) error {
    pipe := r.client.Pipeline()
    for key, value := range values {
        pipe.Set(ctx, key, value, 0)
    }
    _, err := pipe.Exec(ctx)
    if err != nil {
        return err
    }
    return nil
}

func (r *RedisClient) SetWithTTL(ctx context.Context, key string, value string, ttl time.Duration) error {
    err := r.client.Set(ctx, key, value, ttl).Err()
    if err != nil {
        return err
    }
    return nil
}

func (r *RedisClient) GetWithTTL(ctx context.Context, key string) (string, time.Duration, error) {
    val, err := r.client.Get(ctx, key).Result()
    if err != nil {
        if err == redis.Nil {
            return "", 0, nil
        }
        return "", 0, err
    }

    ttl, err := r.client.TTL(ctx, key).Result()
    if err != nil {
        return "", 0, err
    }

    return val, ttl, nil
}

func (r *RedisClient) SetWithDefaultTTL(ctx context.Context, key string, value string) error {
    ttl, exists := r.ttls["default"]
    if !exists {
        return fmt.Errorf("default TTL not set")
    }
    return r.SetWithTTL(ctx, key, value, time.Duration(ttl)*time.Second)
}

func (r *RedisClient) GetWithDefaultTTL(ctx context.Context, key string) (string, time.Duration, error) {
    val, err := r.Get(ctx, key)
    if err != nil {
        return "", 0, err
    }

    ttl, exists := r.ttls["default"]
    if !exists {
        return "", 0, fmt.Errorf("default TTL not set")
    }

    return val, time.Duration(ttl) * time.Second, nil
}


func (r *RedisClient) SetWithCompression(ctx context.Context, key string, value string, ttl time.Duration) error {
    if !r.useCompression {
        return r.Set(ctx, key, value, ttl)
    }
    
    var buf bytes.Buffer
    gz := gzip.NewWriter(&buf)
    
    if _, err := gz.Write([]byte(value)); err != nil {
        return fmt.Errorf("compression failed: %w", err)
    }
    
    if err := gz.Close(); err != nil {
        return err
    }
    
    compressed := buf.String()
    return r.Set(ctx, key, compressed, ttl)
}

func (r *RedisClient) GetWithDecompression(ctx context.Context, key string) (string, error) {
    compressed, err := r.Get(ctx, key)
    if err != nil {
        return "", err
    }
    
    if !r.useCompression {
        return compressed, nil
    }
    
    gr, err := gzip.NewReader(strings.NewReader(compressed))
    if err != nil {
        return "", fmt.Errorf("decompression failed: %w", err)
    }
    defer gr.Close()
    
    data, err := io.ReadAll(gr)
    if err != nil {
        return "", err
    }
    
    return string(data), nil
}


func (r *RedisClient) GetPoolStats() *redis.PoolStats {
    return r.client.PoolStats()
}

func (r *RedisClient) ExportMetrics() map[string]float64 {
    stats := r.GetPoolStats()
    metrics := map[string]float64{
        "cache_hits":         float64(r.metrics.Hits),
        "cache_misses":      float64(r.metrics.Misses),
        "cache_hit_rate":    r.metrics.HitRate,
        "cache_last_reset":  float64(r.metrics.LastReset),
        "pool_total_conns":  float64(stats.TotalConns),
        "pool_idle_conns":   float64(stats.IdleConns),
        "pool_stale_conns":  float64(stats.StaleConns),
    }
    return metrics
}

func (r *RedisClient) withTimeout(ctx context.Context) (context.Context, context.CancelFunc) {
    if r.contextTimeout > 0 {
        return context.WithTimeout(ctx, r.contextTimeout)
    }
    return ctx, func() {}
}


func (r *RedisClient) withRetry(op func() error) error {
    var lastErr error
    for i := 0; i < 3; i++ {
        if err := op(); err != nil {
            lastErr = err
            time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
            continue
        }
        return nil
    }
    return fmt.Errorf("operation failed after retries: %w", lastErr)
}

func (r *RedisClient) Increment(ctx context.Context, key string) (int64, error) {
    return r.client.Incr(ctx, key).Result()
}

func (r *RedisClient) IncrementBy(ctx context.Context, key string, value int64) (int64, error) {
    return r.client.IncrBy(ctx, key, value).Result()
}