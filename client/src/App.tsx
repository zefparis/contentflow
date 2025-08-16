import { Switch, Route, Link, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/ui/theme-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import Home from "@/pages/home";
import Dashboard from "@/pages/dashboard";
import Assets from "@/pages/assets";
import Performance from "@/pages/performance";
import Scheduler from "@/pages/scheduler";
import Settings from "@/pages/settings";
import Orchestrator from "@/pages/orchestrator";
import Partners from "@/pages/partners";
import Byop from "@/pages/byop";
import PartnerAuth from "@/pages/partner-auth";
import PartnerProfile from "@/pages/partner-profile";
import ContentManager from "@/pages/ContentManager";
import SocialConnections from "@/pages/SocialConnections";
import AdminMonitoring from "@/pages/AdminMonitoring";
import NotFound from "@/pages/not-found";
import { Brain, Video, Play, BarChart3, Settings as SettingsIcon, Home as HomeIcon, Bot, Users, Menu, Calendar, Plus, Link as LinkIcon } from "lucide-react";
import { useState } from "react";

function Navigation() {
  const [location] = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  
  const navItems = [
    { path: "/", label: "Accueil", icon: HomeIcon },
    { path: "/dashboard", label: "Dashboard", icon: BarChart3 },
    { path: "/assets", label: "Assets", icon: Video },
    { path: "/performance", label: "Performance IA", icon: Brain },
    { path: "/orchestrator", label: "Orchestrateur IA", icon: Bot },
    { path: "/scheduler", label: "Planificateur", icon: Calendar },
    { path: "/byop", label: "BYOP Creator", icon: Plus },
    { path: "/content-manager", label: "Gérer Contenu", icon: Video },
    { path: "/social-connections", label: "Réseaux Sociaux", icon: LinkIcon },
    { path: "/partners", label: "Partenaires", icon: Users },
    { path: "/partner-auth", label: "Connexion Partenaire", icon: Users },
    { path: "/admin-monitoring", label: "Admin Monitoring", icon: BarChart3 },
    { path: "/settings", label: "Paramètres", icon: SettingsIcon },
  ];

  const isActive = (path: string) => {
    if (path === "/") return location === "/";
    return location.startsWith(path);
  };

  const NavItem = ({ item, onClick }: { item: typeof navItems[0]; onClick?: () => void }) => {
    const Icon = item.icon;
    const active = isActive(item.path);
    
    return (
      <Link href={item.path}>
        <Button
          variant={active ? "default" : "ghost"}
          className={`w-full justify-start gap-2 h-10 text-sm ${
            active 
              ? "bg-blue-600 hover:bg-blue-700 text-white" 
              : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
          }`}
          onClick={onClick}
          data-testid={`nav-${item.path.replace("/", "") || "home"}`}
        >
          <Icon className="h-4 w-4" />
          {item.label}
        </Button>
      </Link>
    );
  };

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
            {navItems.slice(0, 7).map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              
              return (
                <Link key={item.path} href={item.path}>
                  <Button
                    variant={active ? "default" : "ghost"}
                    size="sm"
                    className={`gap-2 ${
                      active 
                        ? "bg-blue-600 hover:bg-blue-700 text-white" 
                        : "text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden xl:inline">{item.label}</span>
                  </Button>
                </Link>
              );
            })}
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-3">
            <Badge variant="secondary" className="hidden sm:flex bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-700">
              <div className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full mr-2"></div>
              Online
            </Badge>
            
            {/* Partner Auth Button - Always visible */}
            <Link href="/partner-auth">
              <Button
                variant="outline"
                size="sm"
                className="bg-orange-50 dark:bg-orange-900 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-700 hover:bg-orange-100 dark:hover:bg-orange-800"
                data-testid="nav-partner-auth"
              >
                <Users className="h-4 w-4 mr-1" />
                <span className="hidden sm:inline">Partenaire</span>
              </Button>
            </Link>
            
            <ThemeToggle />

            {/* Mobile Menu */}
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button variant="outline" size="icon" className="lg:hidden">
                  <Menu className="h-5 w-5" />
                  <span className="sr-only">Ouvrir le menu</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72 sm:w-80 bg-white dark:bg-gray-800 max-h-screen overflow-y-auto">
                <SheetHeader className="text-left">
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
                </SheetHeader>
                
                <div className="mt-6 space-y-1">
                  {navItems.map((item) => (
                    <NavItem
                      key={item.path}
                      item={item}
                      onClick={() => setIsOpen(false)}
                    />
                  ))}
                </div>

                <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="space-y-3">
                    {/* Partner Auth in Mobile Menu */}
                    <Link href="/partner-auth" onClick={() => setIsOpen(false)}>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full h-9 text-sm bg-orange-50 dark:bg-orange-900 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-700 hover:bg-orange-100 dark:hover:bg-orange-800"
                      >
                        <Users className="h-4 w-4 mr-2" />
                        Partenaire
                      </Button>
                    </Link>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                        Statut
                      </span>
                      <Badge variant="secondary" className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-700">
                        <div className="w-1.5 h-1.5 bg-green-500 dark:bg-green-400 rounded-full mr-1.5"></div>
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

function Router() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navigation />
      <main>
        <Switch>
          <Route path="/" component={Home} />
          <Route path="/dashboard" component={Dashboard} />
          <Route path="/assets" component={Assets} />
          <Route path="/performance" component={Performance} />
          <Route path="/orchestrator" component={Orchestrator} />
          <Route path="/scheduler" component={Scheduler} />
          <Route path="/byop" component={Byop} />
          <Route path="/content-manager" component={ContentManager} />
          <Route path="/social-connections" component={SocialConnections} />
          <Route path="/partners" component={Partners} />
          <Route path="/partner-auth" component={PartnerAuth} />
          <Route path="/partner-profile" component={PartnerProfile} />
          <Route path="/admin-monitoring" component={AdminMonitoring} />
          <Route path="/settings" component={Settings} />
          <Route component={NotFound} />
        </Switch>
      </main>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="contentflow-ui-theme">
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
