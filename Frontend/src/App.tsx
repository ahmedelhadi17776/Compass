import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/dashboard/Dashboard';
import HealthDashboard from './components/health/HealthDashboard';
import Home from './components/home/Home';
import Workflow from './components/workflow/Workflow';
import { Tasks } from './components/tasks/Tasks';
import Calendar from './components/calendar/Calendar';
import AIAssistant from './components/ai/AIAssistant';
import FocusMode from './components/productivity/FocusMode';
import FileManager from './components/files/FileManager';
import { ThemeProvider } from './contexts/theme-provider';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset } from '@/components/ui/sidebar';
import { Toaster } from '@/components/ui/toaster';
import TitleBar from '@/components/layout/TitleBar';
import { Login } from './components/auth/Login';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('isAuthenticated') === 'true'
  });

  // Protected Route component
  const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
    return isAuthenticated ? children : <Navigate to="/login" replace />;
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
    localStorage.setItem('isAuthenticated', 'true');
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    localStorage.removeItem('isAuthenticated');
  };

  const handleMinimize = () => {
    // implement minimize logic
  };

  const handleMaximize = () => {
    // implement maximize logic
  };

  const handleClose = () => {
    // implement close logic
  };

  return (
    <ThemeProvider defaultTheme="dark" storageKey="aiwa-theme">
      <div className="h-screen flex flex-col overflow-hidden">
        <Router>
          {!isAuthenticated ? (
            <Routes>
              <Route path="*" element={<Login onLogin={() => setIsAuthenticated(true)} />} />
            </Routes>
          ) : (
            <SidebarProvider>
              <AppSidebar />
              <SidebarInset className="flex flex-col">
                <TitleBar 
                  onMinimize={handleMinimize}
                  onMaximize={handleMaximize}
                  onClose={handleClose}
                />
                <main className="flex-1 h-full main-content">
                  <Routes>
                    {/* Auth Routes */}
                    <Route path="/login" element={
                      isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login onLogin={handleLogin} />
                    } />

                    {/* Protected Routes */}
                    <Route path="/" element={
                      <ProtectedRoute>
                        <Navigate to="/dashboard" replace />
                      </ProtectedRoute>
                    } />
                    
                    <Route path="/dashboard" element={
                      <ProtectedRoute>
                          <Dashboard />
                      </ProtectedRoute>
                    } />
                    <Route path="/dashboard/tasks" element={
                      <ProtectedRoute>
                        <Dashboard view="tasks" />
                      </ProtectedRoute>
                    } />
                    <Route path="/dashboard/calendar" element={
                      <ProtectedRoute>
                        <Dashboard view="calendar" />
                      </ProtectedRoute>
                    } />
                    <Route path="/dashboard/monitoring" element={
                      <ProtectedRoute>
                        <Dashboard view="monitoring" />
                      </ProtectedRoute>
                    } />
                    <Route path="/workflow" element={
                      <ProtectedRoute>
                        <Workflow />
                      </ProtectedRoute>
                    } />
                    <Route path="/workflow/builder" element={
                      <ProtectedRoute>
                        <Workflow view="builder" />
                      </ProtectedRoute>
                    } />
                    <Route path="/workflow/templates" element={
                      <ProtectedRoute>
                        <Workflow view="templates" />
                      </ProtectedRoute>
                    } />
                    <Route path="/workflow/history" element={
                      <ProtectedRoute>
                        <Workflow view="history" />
                      </ProtectedRoute>
                    } />
                    <Route path="/health" element={
                      <ProtectedRoute>
                        <HealthDashboard />
                      </ProtectedRoute>
                    } />

                    {/* Tasks & Workflow Routes */}
                    <Route path="/tasks" element={
                      <ProtectedRoute>
                        <Tasks />
                      </ProtectedRoute>
                    } />
                    <Route path="/tasks/create" element={
                      <ProtectedRoute>
                        <Tasks view="create" />
                      </ProtectedRoute>
                    } />
                    <Route path="/tasks/manage" element={
                      <ProtectedRoute>
                        <Tasks view="manage" />
                      </ProtectedRoute>
                    } />
                    <Route path="/tasks/dependencies" element={
                      <ProtectedRoute>
                        <Tasks view="dependencies" />
                      </ProtectedRoute>
                    } />
                    <Route path="/tasks/automation" element={
                      <ProtectedRoute>
                        <Tasks view="automation" />
                      </ProtectedRoute>
                    } />

                    {/* Calendar Routes */}
                    <Route path="/calendar" element={
                      <ProtectedRoute>
                        <Calendar />
                      </ProtectedRoute>
                    } />
                    <Route path="/calendar/sync" element={
                      <ProtectedRoute>
                        <Calendar view="sync" />
                      </ProtectedRoute>
                    } />
                    <Route path="/calendar/schedule" element={
                      <ProtectedRoute>
                        <Calendar view="schedule" />
                      </ProtectedRoute>
                    } />
                    <Route path="/calendar/notes" element={
                      <ProtectedRoute>
                        <Calendar view="notes" />
                      </ProtectedRoute>
                    } />

                    {/* AI Assistant Routes */}
                    <Route path="/ai" element={
                      <ProtectedRoute>
                        <AIAssistant />
                      </ProtectedRoute>
                    } />
                    <Route path="/ai/queries" element={
                      <ProtectedRoute>
                        <AIAssistant view="queries" />
                      </ProtectedRoute>
                    } />
                    <Route path="/ai/reports" element={
                      <ProtectedRoute>
                        <AIAssistant view="reports" />
                      </ProtectedRoute>
                    } />
                    <Route path="/ai/agents" element={
                      <ProtectedRoute>
                        <AIAssistant view="agents" />
                      </ProtectedRoute>
                    } />

                    {/* Productivity Routes */}
                    <Route path="/productivity" element={
                      <ProtectedRoute>
                        <FocusMode />
                      </ProtectedRoute>
                    } />
                    <Route path="/productivity/focus" element={
                      <ProtectedRoute>
                        <FocusMode view="focus" />
                      </ProtectedRoute>
                    } />
                    <Route path="/productivity/metrics" element={
                      <ProtectedRoute>
                        <FocusMode view="metrics" />
                      </ProtectedRoute>
                    } />
                    <Route path="/productivity/wellness" element={
                      <ProtectedRoute>
                        <FocusMode view="wellness" />
                      </ProtectedRoute>
                    } />

                    {/* File Management Routes */}
                    <Route path="/files" element={
                      <ProtectedRoute>
                        <FileManager />
                      </ProtectedRoute>
                    } />
                    <Route path="/files/search" element={
                      <ProtectedRoute>
                        <FileManager view="search" />
                      </ProtectedRoute>
                    } />
                    <Route path="/files/clipboard" element={
                      <ProtectedRoute>
                        <FileManager view="clipboard" />
                      </ProtectedRoute>
                    } />
                    <Route path="/files/organize" element={
                      <ProtectedRoute>
                        <FileManager view="organize" />
                      </ProtectedRoute>
                    } />
                  </Routes>
                </main>
              </SidebarInset>
            </SidebarProvider>
          )}
          <Toaster />
        </Router>
      </div>
    </ThemeProvider>
  );
}

export default App;