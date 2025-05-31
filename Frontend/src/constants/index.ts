export const API_BASE_URL = '/api';

export const CATEGORIES = [
    { value: 'work', label: 'Work' },
    { value: 'personal', label: 'Personal' },
    { value: 'study', label: 'Study' },
    { value: 'health', label: 'Health' },
    { value: 'other', label: 'Other' }
] as const;

export const PRIORITIES = [
    { value: 'high', label: 'High Priority' },
    { value: 'medium', label: 'Medium Priority' },
    { value: 'low', label: 'Low Priority' }
] as const;

export const DATE_RANGES = [
    { value: 'all', label: 'All Dates' },
    { value: 'today', label: 'Today' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' }
] as const;

export const SORT_OPTIONS = [
    { value: 'date', label: 'Date' },
    { value: 'priority', label: 'Priority' },
    { value: 'title', label: 'Title' }
] as const;
