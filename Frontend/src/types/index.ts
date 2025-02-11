export interface Task {
    id: string;
    summary: string;
    description?: string;
    start: {
        dateTime: string;
        timeZone: string;
    };
    end: {
        dateTime: string;
        timeZone: string;
    };
    location?: string;
    htmlLink?: string;
}

export type Priority = 'high' | 'medium' | 'low';
export type ViewType = 'list' | 'calendar';

export interface Category {
    value: string;
    label: string;
}

export interface FilterOption {
    value: string;
    label: string;
}

export interface DateRange {
    start: Date;
    end: Date;
}
