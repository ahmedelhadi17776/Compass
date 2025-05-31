import { cn } from "@/lib/utils"
import React from "react"

interface CustomHeatmapCardProps {
  children: React.ReactNode
  className?: string
}

const CustomHeatmapCard = React.forwardRef<
  HTMLDivElement,
  CustomHeatmapCardProps
>(({ children, className }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border bg-card px-4 py-2 backdrop-blur-lg transition-all",
      "hover:border-zinc-700/30 hover:bg-zinc-900/60 hover:shadow-lg",
      "dark:border-white/10 dark:bg-white/5",
      "dark:hover:border-white/20 dark:hover:bg-white/10",
      className
    )}
  >
    {children}
  </div>
))

CustomHeatmapCard.displayName = "CustomHeatmapCard"

export default CustomHeatmapCard 