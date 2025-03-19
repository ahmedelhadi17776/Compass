import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, FileText, Users, Send, Trash, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useTheme } from "@/contexts/theme-provider"
import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { useLocation, useNavigate } from "react-router-dom"
import { useChat } from "@/contexts/chat-context"
import './AIAssistant.css'

interface AIAssistantProps {
  view?: 'chat' | 'reports' | 'agents'
}

export default function AIAssistant({ view = 'chat' }: AIAssistantProps) {
  const { theme } = useTheme();
  const isDarkMode = theme === 'dark';
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const navigate = useNavigate();
  
  // Use the shared chat context
  const { 
    messages, 
    isLoading, 
    streamingText, 
    sendMessage, 
    resetToDefault 
  } = useChat();
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    
    await sendMessage(input);
    setInput("");
  };

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return 'Just now';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
  };

  // Format markdown-style text to HTML
  const formatMessageContent = (content: string) => {
    // Process line breaks first
    let formattedContent = content.replace(/\n/g, '<br/>');
    
    // Process bold text: **text**
    formattedContent = formattedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Process italic text: *text*
    formattedContent = formattedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Process bullet points
    formattedContent = formattedContent.replace(/- (.*?)(<br\/>|$)/g, '• $1$2');
    
    // Process todo list items: "- [ ]" and "- [x]"
    formattedContent = formattedContent.replace(/• \[ \] (.*?)(<br\/>|$)/g, '<div class="ai-todo-item incomplete">☐ $1</div>$2');
    formattedContent = formattedContent.replace(/• \[x\] (.*?)(<br\/>|$)/g, '<div class="ai-todo-item complete">✓ $1</div>$2');
    
    // Process numbered lists (1. 2. 3. etc)
    formattedContent = formattedContent.replace(/(\d+)\. (.*?)(<br\/>|$)/g, '<div class="ai-list-item">$1. $2</div>$3');
    
    // Process headings ## and ###
    formattedContent = formattedContent.replace(/#{3} (.*?)(<br\/>|$)/g, '<h3 class="ai-heading-3">$1</h3>$2');
    formattedContent = formattedContent.replace(/#{2} (.*?)(<br\/>|$)/g, '<h2 class="ai-heading-2">$1</h2>$2');
    
    // Process code blocks with ```
    formattedContent = formattedContent.replace(/```(.*?)```/gs, '<pre class="ai-code-block">$1</pre>');
    
    // Highlight todo references with their titles
    formattedContent = formattedContent.replace(/"([^"]+)"(\s+todo)?/gi, 
      '<span class="ai-todo-reference">$1</span>');
    
    return formattedContent;
  };
  
  return (
    <div className="flex flex-1 flex-col gap-4 p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">AI Assistant</h2>
      </div>

      <Tabs defaultValue={view} className="space-y-4">
        <TabsList>
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="reports">Reports & Insights</TabsTrigger>
          <TabsTrigger value="agents">Agent Management</TabsTrigger>
        </TabsList>

        <TabsContent value="chat" className="space-y-4">
          <div className="ai-chat-container">
            <div className="ai-chat-header">
              <div className="ai-chat-title">
                <Sparkles className="h-5 w-5 text-muted-foreground" />
                <span>AI Chat Assistant</span>
              </div>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={resetToDefault}
                className="h-8 w-8 p-0"
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="ai-chat-content">
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={cn(
                    "ai-message-row",
                    message.sender === "user" ? "user" : "assistant"
                  )}
                >
                  <div 
                    className={cn(
                      "ai-message-bubble",
                      message.sender === "user" ? "user" : "assistant"
                    )}
                  >
                    {message.sender === "assistant" && (
                      <div className={cn("ai-avatar", "assistant")}>
                        <Sparkles className="h-4 w-4" />
                      </div>
                    )}
                    <div className="ai-message-content">
                      <div className="ai-message-name">
                        {message.sender === "user" ? "You" : "AI Assistant"}
                        <span className="ai-message-timestamp">
                          {formatTimestamp(message.timestamp)}
                        </span>
                      </div>
                      <div 
                        className="ai-message-text"
                        dangerouslySetInnerHTML={{ __html: formatMessageContent(message.text) }}
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Streaming message */}
              {streamingText && (
                <div className="ai-message-row assistant">
                  <div className="ai-message-bubble assistant">
                    <div className="ai-avatar assistant">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div className="ai-message-content">
                      <div className="ai-message-name">AI Assistant</div>
                      <div 
                        className="ai-message-text"
                        dangerouslySetInnerHTML={{ __html: formatMessageContent(streamingText) }}
                      />
                    </div>
                  </div>
                </div>
              )}
              
              {isLoading && !streamingText && (
                <div className="ai-message-row assistant">
                  <div className="ai-message-bubble assistant">
                    <div className="ai-avatar assistant">
                      <Sparkles className="h-4 w-4" />
                    </div>
                    <div className="ai-message-content">
                      <div className="ai-message-name">AI Assistant</div>
                      <div className="ai-typing-indicator">
                        <div className="ai-typing-dot"></div>
                        <div className="ai-typing-dot"></div>
                        <div className="ai-typing-dot"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
            
            <div className="ai-chat-footer">
              <form onSubmit={handleSubmit} className="ai-input-form">
                <Input
                  placeholder={isLoading ? "AI is thinking..." : "Type your message here..."}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  className="ai-chat-input"
                  disabled={isLoading}
                />
                <Button 
                  type="submit" 
                  className="ai-send-button" 
                  disabled={isLoading || !input.trim()}
                >
                  {isLoading ? (
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      <span>Send</span>
                    </>
                  )}
                </Button>
              </form>
            </div>
          </div>
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
  )
}
