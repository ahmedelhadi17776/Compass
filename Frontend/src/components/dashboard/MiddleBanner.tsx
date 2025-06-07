"use client"
import React from "react"
import {
  Card
} from "@/components/ui/card"
import { CheckCircle, Clock, Calendar, ListTodo, Repeat, Sun, Moon, ChevronDown, ChevronUp, ChevronLeft, ChevronRight } from "lucide-react"
import { useEffect, useState, useRef } from "react"

type ItemType = "todo" | "task" | "event" | "habit"

type ScheduleItem = {
  id: string
  title: string
  time: string
  type: ItemType
  completed?: boolean
  icon?: React.ReactNode
}

export function MiddleBanner() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const timelineRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const contentContainerRef = useRef<HTMLDivElement>(null)
  const [expandedRanges, setExpandedRanges] = useState<string[]>([])
  const [showLeftArrow, setShowLeftArrow] = useState(false)
  const [showRightArrow, setShowRightArrow] = useState(false)
  const [containerWidth, setContainerWidth] = useState(0)
  
  // Sample schedule items
  const scheduleItems: ScheduleItem[] = [
    {
      id: "1",
      title: "Breakfast",
      time: "11:30",
      type: "habit",
      completed: false,
      icon: <Repeat className="h-4 w-4 text-white" />
    },
    {
      id: "2",
      title: "Check Email",
      time: "09:00",
      type: "task",
      completed: false,
      icon: <ListTodo className="h-4 w-4 text-white" />
    },
    {
      id: "3",
      title: "Lunch",
      time: "09:30",
      type: "habit",
      completed: false,
      icon: <Repeat className="h-4 w-4 text-white" />
    },
    {
      id: "4",
      title: "Dinner",
      time: "18:00",
      type: "habit",
      completed: false,
      icon: <Repeat className="h-4 w-4 text-white" />
    },
    {
      id: "5",
      title: "Sleep",
      time: "22:00",
      type: "habit",
      completed: false,
      icon: <Repeat className="h-4 w-4 text-white" />
    },
    {
      id: "6",
      title: "Workout",
      time: "09:45",
      type: "habit",
      completed: false,
      icon: <Repeat className="h-4 w-4 text-white" />
    }
  ]

  // Sort items by time for consistent ordering
  const sortedItems = [...scheduleItems].sort((a, b) => {
    const timeA = a.time.split(':').map(Number)
    const timeB = b.time.split(':').map(Number)
    return (timeA[0] * 60 + timeA[1]) - (timeB[0] * 60 + timeB[1])
  })

  // Get unique hour ranges and ensure they're sorted
  const getHourRanges = () => {
    const ranges = new Set<string>()
    sortedItems.forEach(item => {
      const hour = parseInt(item.time.split(':')[0])
      ranges.add(`${hour}-${hour + 1}`)
    })
    return Array.from(ranges).sort((a, b) => {
      const [startA] = a.split('-').map(Number)
      const [startB] = b.split('-').map(Number)
      return startA - startB
    })
  }

  const hourRanges = getHourRanges()

  // Group items by hour range and sort within each group
  const itemsByRange = sortedItems.reduce((acc, item) => {
    const hour = parseInt(item.time.split(':')[0])
    const range = `${hour}-${hour + 1}`
    if (!acc[range]) acc[range] = []
    acc[range].push(item)
    // Sort items within the same hour by minutes
    acc[range].sort((a, b) => {
      const minutesA = parseInt(a.time.split(':')[1])
      const minutesB = parseInt(b.time.split(':')[1])
      return minutesA - minutesB
    })
    return acc
  }, {} as Record<string, ScheduleItem[]>)

  // Calculate spacing constants based on container width
  const getSpacingConstants = () => {
    // Calculate minimum spacing between markers
    const minCardWidth = 160 // Width of a card in pixels
    const minMarkerSpacing = minCardWidth * 1.5 // Minimum space needed between markers
    
    // Determine how many markers can fit
    const actualRangeCount = hourRanges.length
    const paddingSpace = 120 // Space for sun/moon icons and padding (60px on each side)
    const availableWidth = Math.max(containerWidth - paddingSpace, 400) // Available space for markers
    
    // If container width is too small for all markers with minimum spacing,
    // we'll need to scroll
    const needsScroll = availableWidth < (actualRangeCount * minMarkerSpacing)
    
    // Determine the ideal content width
    const contentWidth = needsScroll 
      ? actualRangeCount * minMarkerSpacing + paddingSpace 
      : containerWidth
    
    return {
      contentWidth,
      needsScroll,
      markerSpacing: needsScroll 
        ? minMarkerSpacing 
        : availableWidth / actualRangeCount
    }
  }
  
  // Calculate marker positions with adaptive spacing
  const calculateMarkerPosition = (range: string) => {
    const { markerSpacing, contentWidth } = getSpacingConstants()
    const rangeIndex = hourRanges.indexOf(range)
    
    // Sun icon is at 60px from left, first marker is 60px + markerSpacing/2
    const startPadding = 60 + (markerSpacing / 2)
    
    // Calculate pixel position
    const pixelPosition = startPadding + (rangeIndex * markerSpacing)
    
    // Return pixel position (rather than percentage)
    return pixelPosition
  }
  
  // Toggle expanded state for a range
  const toggleRangeExpand = (range: string) => {
    setExpandedRanges(prev => 
      prev.includes(range) 
        ? prev.filter(r => r !== range) 
        : [...prev, range]
    )
  }
  
  // Check if a range is expanded
  const isRangeExpanded = (range: string) => {
    return expandedRanges.includes(range)
  }
  
  // Handle scroll actions
  const handleScroll = (direction: 'left' | 'right') => {
    if (!scrollContainerRef.current) return
    
    const scrollAmount = 200 // Amount to scroll each time
    const currentScroll = scrollContainerRef.current.scrollLeft
    const newScroll = direction === 'left' 
      ? currentScroll - scrollAmount 
      : currentScroll + scrollAmount
    
    scrollContainerRef.current.scrollTo({
      left: newScroll,
      behavior: 'smooth'
    })
  }
  
  // Check for scroll shadows
  const checkScrollShadows = () => {
    if (!scrollContainerRef.current) return
    
    const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current
    
    // Show left arrow if we're not at the start
    setShowLeftArrow(scrollLeft > 10)
    
    // Show right arrow if we're not at the end
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10)
  }
  
  // Update current time
  useEffect(() => {
    const updateTime = () => {
      setCurrentTime(new Date())
    }
    
    updateTime()
    const interval = setInterval(updateTime, 60000) // Update every minute
    
    return () => {
      clearInterval(interval)
    }
  }, [])
  
  // Track container width and check scroll status
  useEffect(() => {
    const updateDimensions = () => {
      if (scrollContainerRef.current) {
        setContainerWidth(scrollContainerRef.current.clientWidth)
      }
      checkScrollShadows()
    }
    
    // Initial check
    updateDimensions()
    
    // Add event listeners
    window.addEventListener('resize', updateDimensions)
    if (scrollContainerRef.current) {
      scrollContainerRef.current.addEventListener('scroll', checkScrollShadows)
    }
    
    return () => {
      window.removeEventListener('resize', updateDimensions)
      if (scrollContainerRef.current) {
        scrollContainerRef.current.removeEventListener('scroll', checkScrollShadows)
      }
    }
  }, [])
  
  // Update content container width when container width or hour ranges change
  useEffect(() => {
    if (contentContainerRef.current && containerWidth > 0) {
      const { contentWidth } = getSpacingConstants()
      contentContainerRef.current.style.width = `${contentWidth}px`
      
      // Force check scroll shadows after width change
      checkScrollShadows()
    }
  }, [containerWidth, hourRanges.length])

  const { contentWidth } = getSpacingConstants()

  return (
    <Card className="flex flex-col rounded-3xl w-full h-[354px] p-5 shadow-lg bg-zinc-900 text-white overflow-hidden">
      {/* Heading section */}
      <div className="flex flex-col mb-4">
        <span className="text-xs text-zinc-500 mt-1">Today</span>
        <span className="text-xl font-medium text-zinc-200">Daily Timeline</span>
      </div>
      
      {/* Main content area - takes most of the space */}
      <div className="relative flex-1 w-full flex flex-col">
        {/* Scroll Container - Wraps all timeline content */}
        <div 
          ref={scrollContainerRef}
          className="relative flex-1 w-full overflow-x-auto scrollbar-hide"
          style={{ scrollbarWidth: 'none' }}
        >
          <div 
            ref={contentContainerRef}
            className="relative h-full"
            style={{ 
              width: `${contentWidth}px`,
              minWidth: '100%'
            }}
          >
            {/* Schedule Items Display */}
            {hourRanges.map((range) => {
              const pixelPosition = calculateMarkerPosition(range)
              const itemsInRange = itemsByRange[range] || []
              const expanded = isRangeExpanded(range)
              const hasMoreItems = itemsInRange.length > 2
              
              // Get first 2 items and remaining items separately
              const visibleItems = [...itemsInRange].reverse().slice(0, 2)
              const expandedItems = [...itemsInRange].reverse().slice(2)
              
              return (
                <React.Fragment key={range}>
                  {/* Always visible items (max 2) */}
                  {visibleItems.map((item, index) => (
                    <div
                      key={item.id}
                      className="absolute space-y-2"
                      style={{ 
                        left: `${pixelPosition}px`,
                        transform: 'translateX(-45%)',
                        bottom: `${60 + (index * 80)}px` // Position from bottom, earlier events are lower
                      }}
                    >
                      <div
                        className="bg-[#252525] rounded-lg p-3 w-40 text-sm cursor-pointer hover:bg-[#303030] transition-colors"
                        tabIndex={0}
                        aria-label={`${item.title} at ${item.time}`}
                      >
                        <div className="text-sm font-medium text-white mb-1">{item.title}</div>
                        <div className="flex items-center justify-between">
                          <div className="text-xs text-gray-400">
                            {item.time}
                          </div>
                          <div className="rounded-full p-1">
                            {item.icon}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Show more indicator */}
                  {hasMoreItems && (
                    <div 
                      className="absolute cursor-pointer"
                      style={{ 
                        left: `${pixelPosition}px`,
                        transform: 'translateX(-45%)',
                        bottom: `${60 + (visibleItems.length * 80)}px`
                      }}
                      onClick={() => toggleRangeExpand(range)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          toggleRangeExpand(range)
                        }
                      }}
                      tabIndex={0}
                      aria-label={expanded ? "Show less" : `Show ${itemsInRange.length - 2} more items`}
                    >
                      <Card className="bg-[#252525] rounded-md h-[20px] w-[160px] cursor-pointer hover:bg-[#303030] transition-colors flex items-center justify-center">
                        <ChevronUp 
                          className={`h-4 w-4 text-white transition-transform ${expanded ? 'rotate-180' : ''}`}
                        />
                      </Card>
                    </div>
                  )}
                  
                  {/* Dropdown for expanded items */}
                  {expanded && expandedItems.length > 0 && (
                    <div 
                      className="absolute"
                      style={{ 
                        left: `${pixelPosition}px`,
                        transform: 'translateX(-45%)',
                        bottom: `${60 + (visibleItems.length * 80) + 25}px` // Position above the toggle button
                      }}
                    >
                      <Card className="bg-[#1F1F1F] border border-zinc-800 rounded-lg p-2 w-40 shadow-lg mb-1">
                        <div className="space-y-2 max-h-[180px] overflow-y-auto">
                          {expandedItems.map((item) => (
                            <div
                              key={item.id}
                              className="bg-[#252525] rounded-lg p-2 text-sm cursor-pointer hover:bg-[#303030] transition-colors"
                              tabIndex={0}
                              aria-label={`${item.title} at ${item.time}`}
                            >
                              <div className="text-sm font-medium text-white mb-1">{item.title}</div>
                              <div className="flex items-center justify-between">
                                <div className="text-xs text-gray-400">
                                  {item.time}
                                </div>
                                <div className="rounded-full">
                                  {item.icon}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </Card>
                    </div>
                  )}
                </React.Fragment>
              )
            })}
            
            {/* Timeline */}
            <div className="absolute bottom-0 left-0 right-0 flex items-end">
              <div ref={timelineRef} className="relative w-full h-20">
                {/* Main horizontal line */}
                <div className="absolute left-12 right-12 top-1/2 h-0.5 bg-[#252525]"></div>
                
                {/* Sun icon */}
                <div className="absolute left-4 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-full bg-[#252525]">
                  <Sun className="h-5 w-5 text-gray-400" />
                </div>
                
                {/* Moon icon */}
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center justify-center h-8 w-8 rounded-full bg-[#252525]">
                  <Moon className="h-5 w-5 text-gray-400" />
                </div>
                
                {/* Hour markers with hour numbers on both sides */}
                {hourRanges.map((range) => {
                  const [start, end] = range.split('-').map(Number)
                  const pixelPosition = calculateMarkerPosition(range)
                  
                  return (
                    <div key={range} className="absolute mt-10" style={{ left: `${pixelPosition}px`, transform: 'translateX(-50%)' }}>
                      {/* Circle marker */}
                      <div className="absolute top-0 -translate-y-1/2 h-6 w-6 rounded-full bg-[#252525]"></div>
                      
                      {/* Start hour (to the left) */}
                      <div 
                        className="absolute text-gray-500 text-2xl font-bold -mt-2" 
                        style={{ 
                          left: '-60px', 
                          top: '20px' 
                        }}  
                      >
                        {start.toString().padStart(2, '0')}
                      </div>
                      
                      {/* End hour (to the right) */}
                      <div 
                        className="absolute text-gray-500 text-2xl font-bold -mt-2" 
                        style={{ 
                          left: '55px', 
                          top: '20px' 
                        }}
                      >
                        {end.toString().padStart(2, '0')}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
        
        {/* Left scroll arrow */}
        {showLeftArrow && (
          <button 
            className="absolute left-1 top-1/2 -translate-y-1/2 z-10 h-8 w-8 rounded-full bg-zinc-800 flex items-center justify-center shadow-lg hover:bg-zinc-700 transition-colors"
            onClick={() => handleScroll('left')}
            aria-label="Scroll timeline left"
          >
            <ChevronLeft className="h-5 w-5 text-white" />
          </button>
        )}
        
        {/* Right scroll arrow */}
        {showRightArrow && (
          <button 
            className="absolute right-1 top-1/2 -translate-y-1/2 z-10 h-8 w-8 rounded-full bg-zinc-800 flex items-center justify-center shadow-lg hover:bg-zinc-700 transition-colors"
            onClick={() => handleScroll('right')}
            aria-label="Scroll timeline right"
          >
            <ChevronRight className="h-5 w-5 text-white" />
          </button>
        )}
      </div>
    </Card>
  )
}
