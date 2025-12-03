'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { authApi } from '@/lib/api';
import {
  MapIcon,
  CarIcon,
  MessageSquareIcon,
  LayoutDashboardIcon,
  LogOutIcon,
  MenuIcon,
  XIcon,
  ShieldIcon,
  UsersIcon,
  HelpCircleIcon,
  ServerIcon,
  Car,
  RouteIcon,
  BrainIcon,
  ImageIcon,
  HistoryIcon,
  VideoIcon,
} from 'lucide-react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    
    if (!token) {
      router.push('/login');
      return;
    }

    if (savedUser && !user) {
      setUser(JSON.parse(savedUser));
    }
  }, [router, user, setUser]);

  const handleLogout = () => {
    authApi.logout();
    logout();
    router.push('/login');
  };

  // Determine user role type
  const isAdmin = user && (user.role === 'ADMIN' || user.is_superuser);
  const isDriver = user && (user.role === 'OPERATOR' || user.username?.startsWith('driver'));
  const isCustomer = user && !isAdmin && !isDriver;

  // Build navigation based on role
  let allNavigation: { name: string; href: string; icon: any }[] = [];

  if (isAdmin) {
    // ADMIN VIEW - Full access to everything
    allNavigation = [
      { name: 'Dashboard', href: '/', icon: LayoutDashboardIcon },
      { name: 'Live Map', href: '/map', icon: MapIcon },
      { name: 'Vehicles', href: '/vehicles', icon: CarIcon },
      { name: 'AI Chat', href: '/chat', icon: MessageSquareIcon },
      { name: 'Manage Users', href: '/admin/users', icon: UsersIcon },
      { name: 'Devices', href: '/admin/devices', icon: ServerIcon },
      { name: 'AI Management', href: '/admin/ai', icon: BrainIcon },
      { name: 'FAQs', href: '/admin/faqs', icon: HelpCircleIcon },
    ];
  } else if (isDriver) {
    // DRIVER VIEW - Trip management
    allNavigation = [
      { name: 'Driver Panel', href: '/driver', icon: RouteIcon },
      { name: 'Active Trip', href: '/driver/active', icon: Car },
      { name: 'Camera', href: '/driver/camera', icon: VideoIcon },
      { name: 'My Trips', href: '/trips', icon: HistoryIcon },
    ];
  } else {
    // CUSTOMER/PASSENGER VIEW - Book and track trips
    allNavigation = [
      { name: 'Book Taxi', href: '/book', icon: Car },
      { name: 'My Trips', href: '/trips', icon: HistoryIcon },
      { name: 'Image History', href: '/history', icon: ImageIcon },
    ];
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
          <div className="fixed inset-y-0 left-0 flex flex-col w-64 bg-white">
            <div className="flex items-center justify-between h-16 px-4 border-b">
              <span className="text-xl font-bold text-blue-600">TaxiWatch</span>
              <button onClick={() => setSidebarOpen(false)}>
                <XIcon className="w-6 h-6" />
              </button>
            </div>
            <nav className="flex-1 px-4 py-4 space-y-2">
              {allNavigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100"
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              ))}
            </nav>
            <div className="p-4 border-t">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                  {user.first_name[0]}{user.last_name[0]}
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium">{user.first_name} {user.last_name}</p>
                  <p className="text-xs text-gray-500">{user.role}</p>
                </div>
              </div>
              <Button variant="outline" className="w-full" onClick={handleLogout}>
                <LogOutIcon className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 min-h-0 bg-white border-r">
          <div className="flex items-center h-16 px-4 border-b">
            <span className="text-xl font-bold text-blue-600">TaxiWatch</span>
          </div>
          <nav className="flex-1 px-4 py-4 space-y-2">
            {allNavigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            ))}
          </nav>
          <div className="p-4 border-t">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                {user.first_name[0]}{user.last_name[0]}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium">{user.first_name} {user.last_name}</p>
                <p className="text-xs text-gray-500">{user.role}</p>
              </div>
            </div>
            <Button variant="outline" className="w-full" onClick={handleLogout}>
              <LogOutIcon className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Mobile header */}
        <div className="lg:hidden flex items-center justify-between h-16 px-4 bg-white border-b">
          <button onClick={() => setSidebarOpen(true)}>
            <MenuIcon className="w-6 h-6" />
          </button>
          <span className="text-xl font-bold text-blue-600">TaxiWatch</span>
          <div className="w-6" />
        </div>

        {/* Page content */}
        <main className="p-4 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
