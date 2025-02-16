import React from 'react';
import { Home, Users, Wallet, Layers, UserCheck, MessageCircle, Shield, Sun, Moon, LogOut, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  onLogout: () => void;
  userRole?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onViewChange,
  darkMode,
  onToggleDarkMode,
  onLogout,
  userRole = 'editor'
}) => {
  const { t, i18n } = useTranslation();
  const isRTL = i18n.dir() === 'rtl';

  const menuItems = [
    { id: 'home', icon: Home, label: t('navigation.home'), roles: ['admin', 'editor'] },
    { id: 'students', icon: Users, label: t('navigation.students'), roles: ['admin', 'editor'] },
    { id: 'groups', icon: Layers, label: t('navigation.groups'), roles: ['admin', 'editor'] },
    { id: 'instructors', icon: UserCheck, label: t('navigation.instructors'), roles: ['admin', 'editor'] },
    { id: 'payments', icon: Wallet, label: t('navigation.payments'), roles: ['admin'] },
    { id: 'whatsapp', icon: MessageCircle, label: t('navigation.whatsapp'), roles: ['admin', 'editor'] },
    { id: 'users', icon: Shield, label: t('navigation.users'), roles: ['admin'] },
    { id: 'logs', icon: FileText, label: t('navigation.logs'), roles: ['admin'] },
  ];

  // Filter menu items based on user role
  const filteredMenuItems = menuItems.filter(item => item.roles.includes(userRole.toLowerCase()));

  return (
    <div
      dir={i18n.dir()}
      className={cn(
        "w-64 h-screen flex flex-col transition-colors duration-200 flex-none",
        darkMode ? "bg-[#2c2c2e] text-white" : "bg-white text-gray-900"
      )}>
      <div className="p-6">
        <h1 className={cn(
          "text-2xl font-bold",
          darkMode ? "text-white" : "text-gray-900"
        )}>
          CourSys
        </h1>
      </div>

      <nav className="flex-1">
        <ul className="space-y-2 px-4">
          {filteredMenuItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onViewChange(item.id)}
                  className={cn(
                    "w-full flex items-center px-4 py-2 rounded-lg transition-colors duration-200",
                    currentView === item.id
                      ? (darkMode ? "bg-[#3a3a3c] text-white" : "bg-gray-100 text-blue-600")
                      : (darkMode ? "text-gray-400 hover:bg-[#3a3a3c]" : "text-gray-600 hover:bg-gray-50")
                  )}
                >
                  <Icon className={cn(
                    "w-5 h-5",
                    isRTL ? "ml-3" : "mr-3"
                  )} />
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-auto p-4">
        <button
          onClick={onToggleDarkMode}
          className={cn(
            "w-full flex items-center px-4 py-2 rounded-lg transition-colors duration-200",
            darkMode
              ? "text-gray-400 hover:bg-[#3a3a3c]"
              : "text-gray-600 hover:bg-gray-50"
          )}
        >
          {darkMode ? (
            <Sun className={cn("w-5 h-5", isRTL ? "ml-3" : "mr-3")} />
          ) : (
            <Moon className={cn("w-5 h-5", isRTL ? "ml-3" : "mr-3")} />
          )}
          {darkMode ? t('common.lightMode') : t('common.darkMode')}
        </button>
        <button
          onClick={onLogout}
          className={cn(
            "w-full flex items-center px-4 py-2 rounded-lg transition-colors duration-200 mt-2",
            darkMode
              ? "text-red-400 hover:bg-[#3a3a3c]"
              : "text-red-600 hover:bg-gray-50"
          )}
        >
          <LogOut className={cn("w-5 h-5", isRTL ? "ml-3" : "mr-3")} />
          {t('common.logout')}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;