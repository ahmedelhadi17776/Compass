import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import Dashboard from './components/dashboard/Dashboard';
import HealthDashboard from './components/health/HealthDashboard';
import Workflow from './components/workflow/components/Workflow';
import WorkflowDetailPage from './components/workflow/components/WorkflowDetail';
import {Tasks} from './components/todo/Components/TodoParentPage';
import Calendar from './components/calendar/components/Calendar';
import AIAssistant from './components/ai/AIAssistant';
import FocusMode from './components/productivity/FocusMode';
import FileManager from './components/files/FileManager';
import Notes from './components/notes/Notes';
import { ThemeProvider } from './contexts/theme-provider';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset } from '@/components/ui/sidebar';
import { Toaster } from '@/components/ui/toaster';
import TitleBar from '@/components/layout/TitleBar';
import { Login } from './components/auth/Login';
import { useAuth } from '@/hooks/useAuth';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useQueryClient } from '@tanstack/react-query'
import { QueryClientProvider } from '@tanstack/react-query'
import Chatbot from './components/chatbot/Chatbot';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function App() {
  const queryClient = useQueryClient()
  const { isAuthenticated } = useAuth();

  return (
    <ThemeProvider defaultTheme="dark" storageKey="aiwa-theme">
      <QueryClientProvider client={queryClient}>
        <div className="h-screen flex flex-col overflow-hidden">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <AppSidebar />
                    <SidebarInset className="flex flex-col">
                      <TitleBar darkMode={false} />
                      <main className="flex-1 h-full main-content">
                        <Routes>
                          <Route index element={<Navigate to="/dashboard" replace />} />
                          <Route path="dashboard" element={<Dashboard />} />
                          <Route path="Todos&Habits" element={<Tasks />} />
                          <Route path="calendar" element={<Calendar />} />
                          <Route path="ai" element={<AIAssistant />} />
                          <Route path="focus" element={<FocusMode />} />
                          <Route path="files" element={<FileManager />} />
                          <Route path="health" element={<HealthDashboard />} />
                          <Route path="workflow" element={<Workflow />} />
                          <Route path="workflow/:id" element={<WorkflowDetailPage />} />
                          <Route path="notes" element={<Notes />} />
                        </Routes>
                      </main>
                      <Chatbot />
                    </SidebarInset>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
          </Routes>
          <Toaster />
          
        </div>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;