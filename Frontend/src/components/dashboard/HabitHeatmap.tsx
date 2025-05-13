import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { HeatmapData, HeatmapPeriod } from "@/hooks/useHabitHeatmap"
import { cn } from "@/lib/utils"

interface HeatmapProps {
  title: string
  data: HeatmapData
  loading?: boolean
  error?: Error | null
  period: HeatmapPeriod
  onPeriodChange: (period: HeatmapPeriod) => void
  className?: string
}

export default function HabitHeatmap({
  title,
  data,
  loading,
  error,
  period,
  onPeriodChange,
  className
}: HeatmapProps) {
  const [activeData, setActiveData] = useState<HeatmapData>(data)
  const [activePeriod, setActivePeriod] = useState<HeatmapPeriod>(period)
  
  useEffect(() => {
    setActiveData(data)
  }, [data])
  
  useEffect(() => {
    setActivePeriod(period)
  }, [period])
  
  const handleChangePeriod = (newPeriod: HeatmapPeriod) => {
    setActivePeriod(newPeriod)
    onPeriodChange(newPeriod)
  }
  
  // Determine color intensity based on completion count
  const getColorClass = (count: number) => {
    if (count === 0) return "bg-zinc-800" // No completions
    if (count === 1) return "bg-green-900" // 1 completion
    if (count <= 3) return "bg-green-700" // 2-3 completions
    if (count <= 5) return "bg-green-500" // 4-5 completions
    return "bg-green-400" // 6+ completions
  }
  
  // Generate the last 365 days for year view (or appropriate dates for other views)
  const generateDates = () => {
    const dates: string[] = []
    const today = new Date()
    
    let daysToGenerate = 365 // Default for year
    if (activePeriod === "month") daysToGenerate = 31
    if (activePeriod === "week") daysToGenerate = 7
    
    for (let i = daysToGenerate - 1; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(today.getDate() - i)
      
      // Format date as YYYY-MM-DD with timezone consideration
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const formattedDate = `${year}-${month}-${day}`
      dates.push(formattedDate)
    }
    
    return dates
  }
  
  // Calculate calendar view with weekday alignment
  const calculateCalendarData = () => {
    const dates = generateDates()
    const weeks: string[][] = []
    let currentWeek: string[] = []
    
    // If we're showing a year view, align properly to weekdays
    if (activePeriod === "year") {
      // Fill in empty cells at the beginning
      const firstDate = new Date(dates[0])
      const firstDayOfWeek = firstDate.getDay()
      
      // Add empty strings for days before the start date (Sunday is 0, Saturday is 6)
      for (let i = 0; i < firstDayOfWeek; i++) {
        currentWeek.push("")
      }
    }
    
    // Populate the dates
    dates.forEach((date) => {
      currentWeek.push(date)
      
      // Start a new week every Sunday (or when we reach 7 days)
      if (currentWeek.length === 7) {
        weeks.push([...currentWeek])
        currentWeek = []
      }
    })
    
    // Add the last partial week if needed
    if (currentWeek.length > 0) {
      weeks.push([...currentWeek])
    }
    
    return weeks
  }
  
  const weeks = calculateCalendarData()
  
  return (
    <Card className={cn("col-span-3", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-medium">
          {title}
          {loading && <span className="ml-2 text-sm text-muted-foreground">(Loading...)</span>}
          {error && <span className="ml-2 text-sm text-red-500">Error loading data</span>}
        </CardTitle>
        <Select value={period} onValueChange={(value) => handleChangePeriod(value as HeatmapPeriod)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="week">Last Week</SelectItem>
            <SelectItem value="month">Last Month</SelectItem>
            <SelectItem value="year">Last Year</SelectItem>
          </SelectContent>
        </Select>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="min-w-fit">
            {activePeriod === "year" && (
              <div className="mb-1 flex text-xs text-zinc-500">
                <div className="w-4"></div>
                <div className="mr-[2px] w-4 text-center">M</div>
                <div className="mr-[2px] w-4 text-center">T</div>
                <div className="mr-[2px] w-4 text-center">W</div>
                <div className="mr-[2px] w-4 text-center">T</div>
                <div className="mr-[2px] w-4 text-center">F</div>
                <div className="mr-[2px] w-4 text-center">S</div>
                <div className="w-4 text-center">S</div>
              </div>
            )}
            <div className="flex flex-col gap-[2px]">
              {weeks.map((week, weekIndex) => (
                <div key={weekIndex} className="flex gap-[2px]">
                  {/* Display month label on the first day of month */}
                  {activePeriod === "year" && week[0] && new Date(week[0]).getDate() <= 7 && (
                    <div className="w-4 text-xs text-zinc-500">
                      {new Intl.DateTimeFormat('en', { month: 'short' }).format(new Date(week[0]))[0]}
                    </div>
                  )}
                  {activePeriod === "year" && (!week[0] || new Date(week[0]).getDate() > 7) && (
                    <div className="w-4"></div>
                  )}
                  
                  {week.map((date, dateIndex) => {
                    const completions = date ? activeData[date] || 0 : 0
                    return (
                      <div 
                        key={dateIndex}
                        title={date ? `${new Date(date).toLocaleDateString()}: ${completions} completions` : ""} 
                        className={cn(
                          "h-4 w-4 rounded-sm",
                          date ? getColorClass(completions) : "bg-transparent"
                        )}
                      />
                    )
                  })}
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-end gap-2">
              <div className="flex items-center gap-1 text-xs text-zinc-500">
                <span>Less</span>
                <div className="h-3 w-3 rounded-sm bg-zinc-800"/>
                <div className="h-3 w-3 rounded-sm bg-green-900"/>
                <div className="h-3 w-3 rounded-sm bg-green-700"/>
                <div className="h-3 w-3 rounded-sm bg-green-500"/>
                <div className="h-3 w-3 rounded-sm bg-green-400"/>
                <span>More</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 