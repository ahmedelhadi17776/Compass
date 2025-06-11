import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { fetchHeatmapData } from '@/components/todo/api';

export type HeatmapData = Record<string, number>;
export type HeatmapPeriod = 'week' | 'month';

export const useHabitHeatmap = (userId: string) => {
  const [period, setPeriod] = useState<HeatmapPeriod>('month');

  const { data, isLoading, error } = useQuery({
    queryKey: ['habitHeatmap', userId, period],
    queryFn: () => fetchHeatmapData(period),
    enabled: !!userId,
  });

  return {
    data: data || {},
    loading: isLoading,
    error,
    period,
    setPeriod,
  };
};

export default useHabitHeatmap; 