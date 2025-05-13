import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { fetchHeatmapData } from '@/components/calendar/api';

export type HeatmapData = Record<string, number>;
export type HeatmapPeriod = 'week' | 'month' | 'year';

export const useHabitHeatmap = (userId: string) => {
  const [period, setPeriod] = useState<HeatmapPeriod>('year');

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