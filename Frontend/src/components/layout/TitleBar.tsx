import React from 'react';
import { X, Minus, Square } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useLocation, Link } from 'react-router-dom';

interface TitleBarProps {
  darkMode?: boolean;
}

const TitleBar: React.FC<TitleBarProps> = ({ darkMode = false }) => {
  const location = useLocation();
  const path = location.pathname.split('/').filter(Boolean);

  const handleClose = () => {
    if (window.electron) {
      window.electron.close();
    }
  };

  const handleMinimize = () => {
    if (window.electron) {
      window.electron.minimize();
    }
  };

  const handleMaximize = () => {
    if (window.electron) {
      window.electron.maximize();
    }
  };

  return (
    <header className={cn(
      "h-8 flex items-center justify-between select-none bg-[#1C1C1C] drag-region"
    )}>
      <div className="flex items-center gap-2 px-2 drag-region">
        <div className="relative top-[8px] left-1 no-drag">
          <SidebarTrigger className="-ml-1" />
        </div>
        <div className="relative top-[8px] drag-region">
          <Separator orientation="vertical" className="mx-1 h-4" />
        </div>
        <Breadcrumb className="relative top-[8px] no-drag">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild>
                <Link to="/">Dashboard</Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            {path.length > 0 && (
              <>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>
                    {path[path.length - 1].charAt(0).toUpperCase() + path[path.length - 1].slice(1)}
                  </BreadcrumbPage>
                </BreadcrumbItem>
              </>
            )}
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      <div className={cn(
        "flex items-center no-drag space-x-2 px-4 #1C1C1C ",
        "fixed top-0 right-0 h-11",
      )}>
        <button
          onClick={handleMinimize}
          className={cn(
            "p-1 rounded transition-colors hover:bg-[#2c2c2e] text-gray-400 hover:text-white"
          )}
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          onClick={handleMaximize}
          className={cn(
            "p-1 rounded transition-colors hover:bg-[#2c2c2e] text-gray-400 hover:text-white"
          )}
        >
          <Square className="w-4 h-4" />
        </button>
        <button
          onClick={handleClose}
          className="p-1 hover:bg-red-500 hover:text-white rounded transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

export default TitleBar;