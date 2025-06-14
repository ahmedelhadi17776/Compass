import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, Clock, Target, AlertCircle } from "lucide-react"
import { mockReportData } from "./types/reports"
import { Progress } from "@/components/ui/progress"

export default function Reports() {
  const dashboardData = mockReportData.dashboard;
  const { overall_score, key_insights, recommendations } = dashboardData.report.content;

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card className="bg-muted/50">
        <CardHeader>
          <CardTitle>Report Summary</CardTitle>
          <CardDescription>{dashboardData.report.summary}</CardDescription>
        </CardHeader>
      </Card>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Overall Score</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overall_score}/100</div>
            <Progress value={overall_score} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium">Focus Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3h</div>
            <p className="text-xs text-muted-foreground">Target: 10h daily</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Habits</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">6</div>
            <p className="text-xs text-muted-foreground">No active streaks</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasks Status</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2/4</div>
            <p className="text-xs text-muted-foreground">Tasks overdue</p>
          </CardContent>
        </Card>
      </div>

      {/* Key Insights and Recommendations */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Key Insights</CardTitle>
            <CardDescription>Analysis of your activity patterns</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {key_insights.map((insight, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  <span className="text-muted-foreground">•</span>
                  <span>{insight}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
            <CardDescription>Suggested improvements for better productivity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  <span className="text-muted-foreground">{index + 1}.</span>
                  <span>{recommendation}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
} 