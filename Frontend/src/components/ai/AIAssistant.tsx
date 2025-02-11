import { AppSidebar } from "@/components/app-sidebar"
import { SidebarInset } from "@/components/ui/sidebar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, FileText, Users } from "lucide-react"

interface AIAssistantProps {
  view?: 'queries' | 'reports' | 'agents'
}

export default function AIAssistant({ view = 'queries' }: AIAssistantProps) {
  return (
    <>
        <div className="flex flex-col h-full">
          <div className="flex-1 space-y-4 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
              <h2 className="text-3xl font-bold tracking-tight">AI Assistant</h2>
            </div>
            <Tabs defaultValue={view} className="space-y-4">
              <TabsList>
                <TabsTrigger value="queries">Smart Queries</TabsTrigger>
                <TabsTrigger value="reports">Reports & Insights</TabsTrigger>
                <TabsTrigger value="agents">Agent Management</TabsTrigger>
              </TabsList>
              <TabsContent value="queries" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Smart Query System</CardTitle>
                    <CardDescription>
                      Ask questions about your tasks, emails, or any workspace data
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Add query interface here */}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="reports" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>AI-Generated Reports</CardTitle>
                    <CardDescription>
                      Get insights and analytics about your work patterns
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Add reports interface here */}
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="agents" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>AI Agent Management</CardTitle>
                    <CardDescription>
                      Configure and monitor your AI agents
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                          Task Assistant
                        </CardTitle>
                        <Brain className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">Active</div>
                        <p className="text-xs text-muted-foreground">
                          Managing 3 tasks
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                          Research Agent
                        </CardTitle>
                        <FileText className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">Standby</div>
                        <p className="text-xs text-muted-foreground">
                          Ready for queries
                        </p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">
                          Meeting Assistant
                        </CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">Active</div>
                        <p className="text-xs text-muted-foreground">
                          Monitoring 1 meeting
                        </p>
                      </CardContent>
                    </Card>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </div>
    </>
  )
}
