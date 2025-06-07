"use client"
import {
  Card
} from "@/components/ui/card"
import { Activity, Focus, ClockFading, Brain } from "lucide-react"
import { Progress } from "@/components/ui/progress"

export function FocusTime() {
  return (
    <Card className="flex flex-col w-auto rounded-3xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-medium">Today's Progress</h3>
          <p className="text-sm text-muted-foreground">Keep up the momentum!</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Focus className="h-4 w-4 text-blue-500" />
            <span className="text-sm text-muted-foreground">Focus Score</span>
          </div>
          <div className="text-2xl font-bold">85%</div>
          <Progress value={85} className="h-1.5" />
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <ClockFading className="h-4 w-4 text-blue-500" />
            <span className="text-sm text-muted-foreground">Focus Time</span>
          </div>
          <div className="text-2xl font-bold">2H 30M</div>
          <Progress value={80} className="h-1.5" />
        </div>
      </div>

      <div className="relative h-[100px] mt-auto">
        <div className="absolute inset-0 flex items-end">
          {[40, 65, 45, 80, 55, 85, 60].map((height, i) => (
            <div
              key={i}
              className="flex-1 mx-0.5"
              style={{ height: `${height}%` }}
            >
              <div
                className="w-full h-full rounded-t-sm bg-gradient-to-t from-blue-500/50 to-blue-500/20"
              />
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
