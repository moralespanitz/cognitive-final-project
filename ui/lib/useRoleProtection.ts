'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

type UserRole = 'ADMIN' | 'DRIVER' | 'CUSTOMER' | 'OPERATOR' | 'FLEET_MANAGER' | 'DISPATCHER';

// Define which routes are accessible by which roles
const routePermissions: Record<string, UserRole[]> = {
  // Admin only routes
  '/admin/users': ['ADMIN'],
  '/admin/devices': ['ADMIN'],
  '/admin/ai': ['ADMIN'],
  '/admin/faqs': ['ADMIN'],
  '/vehicles': ['ADMIN'],
  '/map': ['ADMIN'],
  '/chat': ['ADMIN'],
  '/video-monitor': ['ADMIN'],

  // Driver routes
  '/driver': ['DRIVER', 'ADMIN'],
  '/driver/active': ['DRIVER', 'ADMIN'],
  '/driver/camera': ['DRIVER', 'ADMIN'],

  // Customer routes
  '/book': ['CUSTOMER', 'ADMIN'],
  '/history': ['CUSTOMER', 'ADMIN'],

  // Shared routes
  '/trips': ['CUSTOMER', 'DRIVER', 'ADMIN'],
  '/': ['ADMIN', 'DRIVER', 'CUSTOMER', 'OPERATOR', 'FLEET_MANAGER', 'DISPATCHER'],
};

// Get the default redirect for each role
const roleDefaultRoutes: Record<UserRole, string> = {
  'ADMIN': '/',
  'DRIVER': '/driver',
  'CUSTOMER': '/book',
  'OPERATOR': '/',
  'FLEET_MANAGER': '/',
  'DISPATCHER': '/',
};

export function useRoleProtection() {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuthStore();

  useEffect(() => {
    if (!user) return;

    const userRole = user.role as UserRole;

    // Find matching route permission
    let hasAccess = false;

    // Check exact match first
    if (routePermissions[pathname]) {
      hasAccess = routePermissions[pathname].includes(userRole) || user.is_superuser;
    } else {
      // Check prefix matches (for dynamic routes like /trip/[id])
      for (const [route, roles] of Object.entries(routePermissions)) {
        if (pathname.startsWith(route) && route !== '/') {
          hasAccess = roles.includes(userRole) || user.is_superuser;
          break;
        }
      }

      // If no specific permission found, allow access (for routes like /trip/123)
      if (!hasAccess && !Object.keys(routePermissions).some(r => pathname.startsWith(r) && r !== '/')) {
        hasAccess = true;
      }
    }

    // Redirect if no access
    if (!hasAccess) {
      const defaultRoute = roleDefaultRoutes[userRole] || '/';
      router.push(defaultRoute);
    }
  }, [user, pathname, router]);

  return { user, isAdmin: user?.role === 'ADMIN' || user?.is_superuser };
}
