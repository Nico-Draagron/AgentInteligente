import { MessageCircle, Database, Settings, Menu, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";
import logo from "@/assets/logo.jpg";

interface HeaderProps {
  onToggleSidebar?: () => void;
}

const Header = ({ onToggleSidebar }: HeaderProps) => {
  const { theme, setTheme } = useTheme();
  
  return (
    <header className="h-16 border-b bg-card/50 backdrop-blur-md supports-[backdrop-filter]:bg-card/80">
      <div className="flex h-full items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleSidebar}
            className="lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl overflow-hidden bg-gradient-primary p-1 shadow-glow">
              <img 
                src={logo} 
                alt="Logo ONSights" 
                className="h-full w-full object-contain"
              />
            </div>
            <div className="flex gap-2 ml-2">
              {["Anna", "Daniel", "Sandra", "Nicolas"].map((name) => (
                <span key={name} className="bg-yellow-400 text-black px-3 py-1 rounded-lg font-semibold shadow text-xs border border-yellow-600">
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="hover:bg-primary/5">
            <Database className="h-4 w-4" />
            <span className="hidden sm:inline ml-2">Dados</span>
          </Button>
          
          <Button variant="ghost" size="sm" className="hover:bg-primary/5">
            <MessageCircle className="h-4 w-4" />
            <span className="hidden sm:inline ml-2">Histórico</span>
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="hover:bg-accent"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>
          
          <Button variant="ghost" size="sm" className="hover:bg-primary/5">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;