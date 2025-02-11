import React from 'react';
import { Search, Bell } from 'lucide-react';

interface TopNavProps {
  userImage?: string;
}

const TopNav: React.FC<TopNavProps> = ({ 
  userImage = "https://ostermancron.com/wp-content/uploads/2016/02/blank-profile-picture-973460_640-300x300.png",
}) => {
  return (
    <div className="h-14 border-b border-gray-200 flex items-center bg-white absolute top-0 right-0 left-[229px] z-1">
      {/* Left Section with Search Bar */}
      <div className="px-4 flex items-center">
        <div className="relative w-96">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full pl-10 pr-4 py-2 rounded-2xl bg-[#f8f8f8] focus:outline-none border-0 focus:ring-0 appearance-none"
            style={{ WebkitAppearance: 'none' }}
          />
        </div>
      </div>

      {/* Flex Spacer */}
      <div className="flex-1"></div>

      {/* Right Section */}
      <div className="px-4 flex items-center gap-4">
        {/* Notification Bell */}
        <button className="p-2 hover:bg-gray-100 rounded-full relative">
          <Bell className="w-5 h-5 text-gray-600" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* User Profile */}
        <div className="flex items-center">
          <img
            src={userImage}
            alt="Profile"
            className="w-8 h-8 rounded-full object-cover"
          />
          <button className="ml-1 p-1 hover:bg-gray-100 rounded">
            <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default TopNav; 