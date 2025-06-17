import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"
import { useCreateReport, useReportGeneration, useGetReport } from "./hooks"
import { CreateReportPayload, ReportType, DashboardReportContent, ActivityReportContent, ProductivityReportContent } from "./types"
import { useAuth } from "@/hooks/useAuth"

export default function Reports() {
  const { user } = useAuth();
  const [title, setTitle] = useState("Productivity Report");
  const [type, setType] = useState<ReportType>("productivity");
  const [startDate, setStartDate] = useState("2025-06-01");
  const [endDate, setEndDate] = useState("2025-06-14");

  const createReportMutation = useCreateReport(user);
  const { data: createdReportData, isPending: isCreating, isError: isCreateError, error: createError } = createReportMutation;

  const reportId = createdReportData?.report_id || null;
  const { progress, startGeneration, isGenerating, isGenerationComplete } = useReportGeneration(reportId);
  
  const { data: reportData, isFetching: isFetchingReport, isError: isFetchError, error: fetchError } = useGetReport(
    isGenerationComplete ? reportId : null
  );

  const handleCreateReport = () => {
    const payload: CreateReportPayload = {
      title,
      type,
      time_range: {
        start_date: startDate,
        end_date: endDate,
      },
    };
    createReportMutation.mutate(payload);
  };

  if (!user) {
    return (
      <div className="flex justify-center items-center h-full">
        <p>Please log in to create reports.</p>
      </div>
    );
  }

  if (isCreating) {
    return (
      <div className="flex justify-center items-center h-full">
        <p>Creating report...</p>
      </div>
    );
  }

  if (isCreateError) {
    return (
      <div className="flex justify-center items-center h-full">
        <p>Error creating report: {createError?.message}</p>
      </div>
    );
  }

  if (reportData && reportData.parsedContent) {
    const { parsedContent, type } = reportData;

    const renderDashboardContent = () => {
      const content = parsedContent.content as DashboardReportContent;
      return (
        <>
          <div className="mb-6 flex flex-row gap-4">
            <Card className="flex-1">
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p>{parsedContent.summary}</p>
              </CardContent>
            </Card>

            <Card className="w-[120px]">
              <CardHeader className="text-center">
                <CardTitle>Overall Score</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-5xl font-bold text-center">{content.overall_score}</p>
              </CardContent>
            </Card>
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
              <Card>
                  <CardHeader><CardTitle>Key Insights</CardTitle></CardHeader>
                  <CardContent>
                      <ul className="list-disc pl-5 space-y-2">
                          {content.key_insights.map((insight: string, index: number) => <li key={index}>{insight}</li>)}
                      </ul>
                  </CardContent>
              </Card>
              <Card>
                  <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
                  <CardContent>
                      <ul className="list-disc pl-5 space-y-2">
                          {content.recommendations.map((rec: string, index: number) => <li key={index}>{rec}</li>)}
                      </ul>
                  </CardContent>
              </Card>
          </div>
        </>
      )
    }

    const renderActivityContent = () => {
        const content = parsedContent.content as ActivityReportContent;
        return (
            <>
                <div className="mb-6 flex flex-row gap-4">
                    <Card className="flex-1">
                        <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
                        <CardContent><p>{parsedContent.summary}</p></CardContent>
                    </Card>
                    <Card className="w-[120px]">
                        <CardHeader className="text-center"><CardTitle>Activity Score</CardTitle></CardHeader>
                        <CardContent><p className="text-5xl font-bold text-center">{content.activity_score}</p></CardContent>
                    </Card>
                </div>
                <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <Card>
                        <CardHeader><CardTitle>Key Metrics</CardTitle></CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                <li><strong>Tasks Completed:</strong> {content.key_metrics.tasks_completed}</li>
                                <li><strong>Overdue Tasks:</strong> {content.key_metrics.overdue_tasks}</li>
                                <li><strong>Meetings Attended:</strong> {content.key_metrics.meetings_attended}</li>
                                <li><strong>Total Meeting Time:</strong> {content.key_metrics.total_meeting_time_minutes} minutes</li>
                            </ul>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader><CardTitle>Insights</CardTitle></CardHeader>
                        <CardContent>
                            <ul className="list-disc pl-5 space-y-2">
                                {content.insights.map((insight: string, index: number) => <li key={index}>{insight}</li>)}
                            </ul>
                        </CardContent>
                    </Card>
                </div>
            </>
        )
    }

    const renderProductivityContent = () => {
        const content = parsedContent.content as ProductivityReportContent;
        return (
            <>
                <div className="mb-6 flex flex-row gap-4">
                    <Card className="flex-1">
                        <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
                        <CardContent><p>{parsedContent.summary}</p></CardContent>
                    </Card>
                    <Card className="w-[150px]">
                        <CardHeader className="text-center"><CardTitle>Productivity Score</CardTitle></CardHeader>
                        <CardContent><p className="text-5xl font-bold text-center">{content.productivity_score}</p></CardContent>
                    </Card>
                </div>
                <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <Card>
                        <CardHeader><CardTitle>Key Metrics</CardTitle></CardHeader>
                        <CardContent>
                            <ul className="space-y-2">
                                <li><strong>Average Productivity Score:</strong> {content.key_metrics.average_productivity_score}</li>
                                <li><strong>Average Daily Focus Time:</strong> {content.key_metrics.average_daily_focus_time_hours}</li>
                                <li><strong>Task Completion Rate:</strong> {content.key_metrics.task_completion_rate}</li>
                                <li><strong>Tasks Completed:</strong> {content.key_metrics.tasks_completed}</li>
                                <li><strong>Meeting Time:</strong> {content.key_metrics.meeting_time_minutes} minutes</li>
                                <li><strong>Number of Meetings:</strong> {content.key_metrics.number_of_meetings}</li>
                            </ul>
                        </CardContent>
                    </Card>
                    <div className="space-y-6">
                        <Card>
                            <CardHeader><CardTitle>Insights</CardTitle></CardHeader>
                            <CardContent>
                                <ul className="list-disc pl-5 space-y-2">
                                    {content.insights.map((insight: string, index: number) => <li key={index}>{insight}</li>)}
                                </ul>
                            </CardContent>
                        </Card>
                        <Card>
                            <CardHeader><CardTitle>Areas for Improvement</CardTitle></CardHeader>
                            <CardContent>
                                <ul className="list-disc pl-5 space-y-2">
                                    {content.areas_for_improvement.map((area: string, index: number) => <li key={index}>{area}</li>)}
                                </ul>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </>
        )
    }

    return (
      <div className="p-8 h-full overflow-y-auto">
        <h1 className="text-3xl font-bold mb-2">{reportData.title}</h1>
        {reportData.completed_at && (
          <p className="text-gray-500 dark:text-gray-400 mb-6">Report generated on {new Date(reportData.completed_at).toLocaleString()}</p>
        )}
        
        {type === 'dashboard' && renderDashboardContent()}
        {type === 'activity' && renderActivityContent()}
        {type === 'productivity' && renderProductivityContent()}

        <div>
          <h2 className="text-2xl font-bold mb-4">Detailed Sections</h2>
          <div className="space-y-4">
            {parsedContent.sections.map((section, index) => (
              <Card key={index}>
                <CardHeader><CardTitle>{section.title}</CardTitle></CardHeader>
                <CardContent>
                  <p>{section.content}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }
  
  if (isGenerating) {
    return (
        <div className="flex flex-col justify-center items-center h-full space-y-4">
            <p>Generating Report: {progress?.message || 'Connecting...'}</p>
            {progress && <p>Progress: {Math.round(progress.progress * 100)}%</p>}
        </div>
    );
  }
  
  if (isFetchingReport) {
    return (
        <div className="flex flex-col justify-center items-center h-full space-y-4">
            <p>Generation complete! Fetching report...</p>
        </div>
    );
  }

  if (isFetchError) {
    return (
      <div className="flex justify-center items-center h-full">
        <p>Error fetching report: {fetchError?.message}</p>
      </div>
    );
  }

  if (reportData && !reportData.parsedContent) {
    return (
        <div className="flex justify-center items-center h-full">
            <p>Report fetched, but content is not in the expected format.</p>
        </div>
    )
  }

  if (reportId) {
    return (
      <div className="flex flex-col justify-center items-center h-full space-y-4">
        <p>Report created with ID: {reportId}</p>
        <Button size="lg" onClick={startGeneration} disabled={isGenerating}>
          {isGenerating ? 'Generating...' : 'Generate Report'}
        </Button>
      </div>
    );
  }

  return (
    <div className="p-8 h-full overflow-y-auto">
      <Card className="w-full max-w-3xl mx-auto mt-[120px]">
        <CardHeader>
          <CardTitle>Create a new Report</CardTitle>
          <CardDescription>Fill in the details below to create a new report.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Enter report title" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="type">Type</Label>
              <Select onValueChange={(value: ReportType) => setType(value)} defaultValue={type}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a report type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="productivity">Productivity</SelectItem>
                  <SelectItem value="activity">Activity</SelectItem>
                  <SelectItem value="dashboard">Dashboard</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-date">Start Date</Label>
                <Input id="start-date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end-date">End Date</Label>
                <Input id="end-date" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
            </div>
            <Button onClick={handleCreateReport} className="w-full">
              Create Report
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 