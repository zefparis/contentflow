import { useState } from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Video,
  Menu,
  Home,
  BarChart3,
  Video as VideoIcon,
  TrendingUp,
  Bot,
  Calendar,
  Settings,
  Users,
  X
} from "lucide-react";

const navigationItems = [
  { href: "/", label: "Accueil", icon: Home },
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/assets", label: "Assets", icon: VideoIcon },
  { href: "/performance", label: "Performance", icon: TrendingUp },
  { href: "/orchestrator", label: "AI Orchestrator", icon: Bot },
  { href: "/scheduler", label: "Scheduler", icon: Calendar },
  { href: "/partners", label: "Partenaires", icon: Users },
  { href: "/settings", label: "Paramètres", icon: Settings },
];

export function Navbar() {
  const [location] = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") return location === "/";
    return location.startsWith(href);
  };

  const NavItem = ({ href, label, icon: Icon, onClick }: { 
    href: string; 
    label: string; 
    icon: any; 
    onClick?: () => void;
  }) => (
    <Link href={href}>
      <Button
        variant={isActive(href) ? "default" : "ghost"}
        className={`w-full justify-start gap-3 h-12 ${
          isActive(href) 
            ? "bg-blue-600 hover:bg-blue-700 text-white" 
            : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
        }`}
        onClick={onClick}
        data-testid={`nav-${href.replace("/", "") || "home"}`}
      >
        <Icon className="h-5 w-5" />
        {label}
      </Button>
    </Link>
  );

  return (
    <nav className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/">
            <div className="flex items-center space-x-3 cursor-pointer">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Video className="h-6 w-6 text-white" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">ContentFlow</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Automated Content Pipeline</p>
              </div>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center space-x-1">
            {navigationItems.slice(0, 6).map((item) => (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive(item.href) ? "default" : "ghost"}
                  size="sm"
                  className={`gap-2 ${
                    isActive(item.href) 
                      ? "bg-blue-600 hover:bg-blue-700 text-white" 
                      : "text-gray-700 dark:text-gray-300"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="hidden xl:inline">{item.label}</span>
                </Button>
              </Link>
            ))}
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-3">
            <Badge variant="secondary" className="hidden sm:flex bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-700">
              <div className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full mr-2"></div>
              Online
            </Badge>
            
            <ThemeToggle />

            {/* Mobile Menu */}
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="lg:hidden">
                  <Menu className="h-5 w-5" />
                  <span className="sr-only">Ouvrir le menu</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-80 bg-white dark:bg-gray-800">
                <SheetHeader className="text-left">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                        <Video className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <SheetTitle className="text-lg font-bold text-gray-900 dark:text-white">
                          ContentFlow
                        </SheetTitle>
                        <SheetDescription className="text-gray-600 dark:text-gray-400">
                          Menu de navigation
                        </SheetDescription>
                      </div>
                    </div>
                  </div>
                </SheetHeader>
                
                <div className="mt-8 space-y-2">
                  {navigationItems.map((item) => (
                    <NavItem
                      key={item.href}
                      href={item.href}
                      label={item.label}
                      icon={item.icon}
                      onClick={() => setIsOpen(false)}
                    />
                  ))}
                </div>

                <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Statut système
                      </span>
                      <Badge variant="secondary" className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-700">
                        <div className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full mr-2"></div>
                        En ligne
                      </Badge>
                    </div>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </div>
    </nav>
  );
}