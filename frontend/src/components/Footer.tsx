import Link from "next/link";
import { Share2, ThumbsUp, Rss, Globe } from "lucide-react";

export default function Footer() {
  return (
    <footer className="w-full py-16 px-4 md:px-10 bg-surface-bright dark:bg-on-surface border-t border-outline-variant dark:border-outline mt-auto">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="flex flex-col gap-4">
          <span className="text-lg font-bold font-plus-jakarta text-on-surface dark:text-surface-bright">RoomNest</span>
          <p className="text-sm text-on-surface-variant dark:text-surface-variant">
            Redefining premium living spaces for the modern explorer.
          </p>
          <div className="flex gap-4 mt-2">
            <a href="#" className="w-8 h-8 rounded-full border border-outline-variant flex items-center justify-center hover:bg-primary-container hover:text-white transition-all">
              <Share2 className="w-4 h-4" />
            </a>
            <a href="#" className="w-8 h-8 rounded-full border border-outline-variant flex items-center justify-center hover:bg-primary-container hover:text-white transition-all">
              <ThumbsUp className="w-4 h-4" />
            </a>
            <a href="#" className="w-8 h-8 rounded-full border border-outline-variant flex items-center justify-center hover:bg-primary-container hover:text-white transition-all">
              <Rss className="w-4 h-4" />
            </a>
          </div>
        </div>
        
        <div>
          <h5 className="text-xs font-bold text-on-primary-fixed-variant uppercase tracking-wider mb-4">Platform</h5>
          <ul className="space-y-3">
            <li><Link href="/search" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Browse Properties</Link></li>
            <li><Link href="/add-property" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">List Property</Link></li>
            <li><Link href="/search?type=PG" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">PG & Hostels</Link></li>
          </ul>
        </div>
        
        <div>
          <h5 className="text-xs font-bold text-on-primary-fixed-variant uppercase tracking-wider mb-4">Resources</h5>
          <ul className="space-y-3">
            <li><Link href="/blog" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Stay Blog</Link></li>
            <li><a href="#" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Owner Guides</a></li>
            <li><a href="#" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Support Center</a></li>
          </ul>
        </div>
        
        <div>
          <h5 className="text-xs font-bold text-on-primary-fixed-variant uppercase tracking-wider mb-4">Legal</h5>
          <ul className="space-y-3">
            <li><a href="#" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Privacy Policy</a></li>
            <li><a href="#" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Terms of Service</a></li>
            <li><a href="#" className="text-sm text-on-surface-variant dark:text-surface-variant hover:text-primary transition-colors">Cookie Policy</a></li>
          </ul>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto mt-12 pt-8 border-t border-outline-variant/30 flex flex-wrap justify-between items-center gap-4">
        <p className="text-xs text-on-surface-variant dark:text-surface-variant">© 2026 RoomNest. Premium Living Spaces.</p>
        <div className="flex gap-6 text-xs text-on-surface-variant">
          <span className="flex items-center gap-1"><Globe className="w-3.5 h-3.5" /> English (US)</span>
          <span>₹ INR</span>
        </div>
      </div>
    </footer>
  );
}
