"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Search, MapPin, Home, ShieldCheck, Star, Calendar, 
  Building, Users, Landmark, UserCheck, Briefcase, ChevronRight, CheckCircle2
} from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [listings, setListings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Search form state
  const [location, setLocation] = useState("");
  const [type, setType] = useState("Apartment");
  const [maxPrice, setMaxPrice] = useState("");
  const [moveInDate, setMoveInDate] = useState("");

  useEffect(() => {
    fetch("/api/listings/")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setListings(data.slice(0, 3)); // Featured properties: first 3 listings
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load listings:", err);
        setLoading(false);
      });
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (location) params.append("query", location);
    if (type) params.append("type", type);
    if (maxPrice) params.append("max_price", maxPrice);
    router.push(`/search?${params.toString()}`);
  };

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative w-full h-[650px] md:h-[750px] flex items-center justify-center overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center transition-transform duration-[10000ms] ease-out scale-100 hover:scale-105"
          style={{ 
            backgroundImage: "url('https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1920&q=80')",
            filter: "brightness(0.55)"
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/20 via-black/40 to-black/60" />
        
        <div className="relative z-10 w-full max-w-7xl px-6 md:px-10 text-center text-white">
          <h1 className="text-4xl md:text-6xl font-extrabold font-plus-jakarta mb-6 tracking-tight drop-shadow-lg leading-tight max-w-4xl mx-auto">
            Find Your Perfect Home Without the Stress
          </h1>
          <p className="text-base md:text-xl font-medium text-white/90 mb-8 max-w-2xl mx-auto">
            Zero brokerage, verified properties, and digital documentation support.
          </p>

          {/* Search Box */}
          <form onSubmit={handleSearch} className="bg-white p-4 rounded-2xl md:rounded-full shadow-2xl max-w-5xl mx-auto flex flex-col md:flex-row gap-4 items-center border border-outline-variant/30 text-on-surface">
            <div className="flex-1 w-full border-b md:border-b-0 md:border-r border-outline-variant/50 pb-3 md:pb-0 md:px-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Location</label>
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-primary shrink-0" />
                <input 
                  type="text" 
                  placeholder="City or Area" 
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold placeholder:text-outline-variant bg-transparent"
                />
              </div>
            </div>

            <div className="flex-1 w-full border-b md:border-b-0 md:border-r border-outline-variant/50 pb-3 md:pb-0 md:px-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Type</label>
              <div className="flex items-center gap-2">
                <Home className="w-5 h-5 text-primary shrink-0" />
                <select 
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold bg-transparent"
                >
                  <option value="Apartment">Apartment</option>
                  <option value="PG (Men)">PG (Men)</option>
                  <option value="PG (Women)">PG (Women)</option>
                  <option value="Co-living">Co-living</option>
                  <option value="Single Room">Single Room</option>
                </select>
              </div>
            </div>

            <div className="flex-1 w-full border-b md:border-b-0 md:border-r border-outline-variant/50 pb-3 md:pb-0 md:px-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Budget</label>
              <div className="flex items-center gap-2">
                <span className="text-primary font-bold text-sm shrink-0">₹</span>
                <input 
                  type="number"
                  placeholder="Max Price"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold placeholder:text-outline-variant bg-transparent"
                />
              </div>
            </div>

            <div className="flex-1 w-full pb-3 md:pb-0 md:px-4">
              <label className="block text-left text-[10px] font-bold text-outline uppercase tracking-wider mb-1">Move In</label>
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-primary shrink-0" />
                <input 
                  type="text"
                  placeholder="Select Date"
                  value={moveInDate}
                  onChange={(e) => setMoveInDate(e.target.value)}
                  onFocus={(e) => (e.target.type = "date")}
                  onBlur={(e) => (e.target.type = "text")}
                  className="w-full border-none focus:outline-none focus:ring-0 text-sm font-semibold placeholder:text-outline-variant bg-transparent"
                />
              </div>
            </div>

            <button type="submit" className="w-full md:w-auto bg-primary hover:bg-primary-container text-white p-4 rounded-xl md:rounded-full flex items-center justify-center transition-all active:scale-95 shadow-lg shadow-primary/20 shrink-0">
              <Search className="w-6 h-6" />
            </button>
          </form>

          <div className="mt-8 flex items-center justify-center gap-4 flex-wrap">
            <span className="text-white/80 text-sm font-semibold">Popular:</span>
            <Link href="/search?city=bangalore" className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-white text-xs font-semibold border border-white/20 hover:bg-white/20 transition-all">Bangalore</Link>
            <Link href="/search?city=mysore" className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-md text-white text-xs font-semibold border border-white/20 hover:bg-white/20 transition-all">Mysore</Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-surface-container-low border-b border-outline-variant/30">
        <div className="max-w-7xl mx-auto px-6 md:px-10 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div>
            <div className="text-3xl md:text-5xl font-extrabold text-primary font-plus-jakarta">12k+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Verified Rooms</div>
          </div>
          <div>
            <div className="text-3xl md:text-5xl font-extrabold text-primary font-plus-jakarta">500+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Happy Owners</div>
          </div>
          <div>
            <div className="text-3xl md:text-5xl font-extrabold text-primary font-plus-jakarta">25+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">Major Cities</div>
          </div>
          <div>
            <div className="text-3xl md:text-5xl font-extrabold text-primary font-plus-jakarta">1M+</div>
            <div className="text-xs text-on-surface-variant font-bold uppercase tracking-wider mt-2">App Users</div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-20 max-w-7xl mx-auto px-6 md:px-10 w-full">
        <div className="flex flex-col items-center mb-12">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">Explore by Category</h2>
          <div className="w-20 h-1 bg-primary rounded-full"></div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          {[
            { type: "Apartment", label: "Apartments", desc: "Full homes for families", icon: <Building className="w-8 h-8 text-primary" /> },
            { type: "PG (Men)", label: "PG / Hostel", desc: "Shared student living", icon: <Users className="w-8 h-8 text-primary" /> },
            { type: "Independent", label: "Independent", desc: "Private villa style", icon: <Landmark className="w-8 h-8 text-primary" /> },
            { type: "Flatmate", label: "Flatmates", desc: "Find a room partner", icon: <UserCheck className="w-8 h-8 text-primary" /> },
            { type: "Co-living", label: "Co-living", desc: "Designed for professionals", icon: <Briefcase className="w-8 h-8 text-primary" /> }
          ].map((cat, idx) => (
            <Link 
              key={idx}
              href={`/search?type=${cat.type}`}
              className="bg-white p-8 rounded-2xl text-center property-card-shadow transition-all duration-300 hover:-translate-y-2 border border-outline-variant/30 flex flex-col items-center group cursor-pointer"
            >
              <div className="w-16 h-16 bg-surface-container rounded-full flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-colors [&_svg]:group-hover:text-white">
                {cat.icon}
              </div>
              <h3 className="text-sm font-bold text-on-surface mb-1">{cat.label}</h3>
              <p className="text-xs text-on-surface-variant">{cat.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Featured Properties */}
      <section className="py-20 bg-surface-container-lowest border-t border-b border-outline-variant/30">
        <div className="max-w-7xl mx-auto px-6 md:px-10">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 gap-4">
            <div>
              <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">Featured Premium Properties</h2>
              <p className="text-sm text-on-surface-variant">Handpicked listings with the highest trust score.</p>
            </div>
            <Link href="/search" className="text-primary font-bold text-sm flex items-center gap-2 hover:underline">
              View All Listings <ChevronRight className="w-4 h-4" />
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((n) => (
                <div key={n} className="bg-white rounded-2xl h-80 animate-pulse border border-outline-variant/20" />
              ))}
            </div>
          ) : listings.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {listings.map((l) => (
                <Link href={`/listing/${l.id}`} key={l.id} className="group bg-white rounded-2xl overflow-hidden property-card-shadow group border border-outline-variant/30 transition-all duration-300 hover:-translate-y-1">
                  <div className="relative h-64 overflow-hidden bg-surface-container-high">
                    {l.image ? (
                      <img 
                        src={l.image} 
                        alt={l.title} 
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-4xl">🏢</div>
                    )}
                    {l.is_verified && (
                      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur text-primary px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 shadow-md">
                        <ShieldCheck className="w-4 h-4 fill-primary text-white" /> Verified
                      </div>
                    )}
                  </div>
                  <div className="p-6">
                    <div className="flex justify-between items-start mb-2 gap-2">
                      <h3 className="text-sm font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">{l.title}</h3>
                      <div className="text-primary font-extrabold text-sm shrink-0">₹{parseFloat(l.price).toLocaleString('en-IN')}<span className="text-[10px] text-on-surface-variant font-normal">/mo</span></div>
                    </div>
                    <p className="text-xs text-on-surface-variant flex items-center gap-1 mb-4">
                      <MapPin className="w-3.5 h-3.5" /> {l.area?.name || l.location}, {l.city?.name || 'Mysore'}
                    </p>
                    <div className="flex items-center gap-4 py-4 border-t border-outline-variant/30 text-[11px] font-semibold text-text-muted">
                      <span>{l.type}</span>
                      <span>•</span>
                      <span>Deposit: ₹{parseFloat(l.deposit).toLocaleString('en-IN')}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-on-surface-variant font-medium">
              No featured listings found. List your property to get started!
            </div>
          )}
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="py-20 max-w-7xl mx-auto px-6 md:px-10 w-full">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">Why Millions Choose RoomNest</h2>
          <p className="text-sm text-on-surface-variant">We bridge the gap between quality living and hassle-free searching.</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-8 bg-surface-container-low rounded-2xl border border-transparent hover:border-primary-container/20 transition-all text-center">
            <div className="mb-6 inline-flex p-4 rounded-2xl bg-primary/10 text-primary">
              <span className="material-symbols-outlined text-4xl">payments</span>
            </div>
            <h3 className="text-lg font-bold mb-4">Zero Brokerage</h3>
            <p className="text-sm text-on-surface-variant">We deal directly with owners. No hidden fees, no unnecessary middleman cuts. Ever.</p>
          </div>
          
          <div className="p-8 bg-surface-container-low rounded-2xl border border-transparent hover:border-primary-container/20 transition-all text-center">
            <div className="mb-6 inline-flex p-4 rounded-2xl bg-secondary-container/10 text-secondary-container">
              <span className="material-symbols-outlined text-4xl">verified_user</span>
            </div>
            <h3 className="text-lg font-bold mb-4">Verified Listings</h3>
            <p className="text-sm text-on-surface-variant">Every single property undergoes a strict 15-point verification process by our ground team.</p>
          </div>

          <div className="p-8 bg-surface-container-low rounded-2xl border border-transparent hover:border-primary-container/20 transition-all text-center">
            <div className="mb-6 inline-flex p-4 rounded-2xl bg-tertiary/10 text-tertiary">
              <span className="material-symbols-outlined text-4xl">contact_support</span>
            </div>
            <h3 className="text-lg font-bold mb-4">Dedicated Support</h3>
            <p className="text-sm text-on-surface-variant">Our concierge service helps you throughout the visiting, booking, and moving process.</p>
          </div>
        </div>
      </section>

      {/* Interactive Map Section */}
      <section className="py-20 bg-on-surface text-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 md:px-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl md:text-5xl font-extrabold font-plus-jakarta mb-6 leading-tight">Find Your Neighborhood Spark</h2>
            <p className="text-base text-surface-variant/80 mb-8">Discover listings by locality. We provide detailed neighborhood insights, from commute times to nearest food hubs.</p>
            <div className="space-y-4">
              {[
                { num: "01", name: "Hitech City, Hyderabad", desc: "420+ Listings • Growing fast", link: "/search?query=hitech%20city" },
                { num: "02", name: "Indiranagar, Bangalore", desc: "350+ Listings • Tech Hub", link: "/search?query=indiranagar" },
                { num: "03", name: "Powai, Mumbai", desc: "280+ Listings • Premium", link: "/search?query=powai" }
              ].map((item, idx) => (
                <Link key={idx} href={item.link} className="flex items-center gap-4 bg-white/5 p-4 rounded-xl border border-white/10 hover:bg-white/10 cursor-pointer transition-all">
                  <span className="text-xl font-bold text-primary">{item.num}</span>
                  <div className="flex-1">
                    <h4 className="text-sm font-bold">{item.name}</h4>
                    <p className="text-xs text-surface-variant/60">{item.desc}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-surface-variant/60" />
                </Link>
              ))}
            </div>
          </div>
          <div className="relative h-[500px] rounded-2xl overflow-hidden shadow-2xl">
            <div 
              className="absolute inset-0 bg-cover bg-center grayscale opacity-30 hover:grayscale-0 hover:opacity-100 transition-all duration-700 cursor-pointer"
              style={{ backgroundImage: "url('https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=1000&q=80')" }}
            />
            {/* Mock Map Pins */}
            <div className="absolute top-1/4 left-1/3 p-3 bg-primary rounded-full shadow-lg border-2 border-white animate-bounce">
              <span className="material-symbols-outlined text-white" style={{ fontVariationSettings: "'FILL' 1" }}>apartment</span>
            </div>
            <div className="absolute bottom-1/3 right-1/4 p-2 bg-secondary-container rounded-full shadow-lg border-2 border-white">
              <span className="material-symbols-outlined text-white" style={{ fontVariationSettings: "'FILL' 1" }}>home</span>
            </div>
            <div className="absolute top-1/2 right-1/2 p-2 bg-white text-primary rounded-lg shadow-xl font-bold px-3 py-1 flex items-center gap-2 text-xs">
              ₹45k <span className="material-symbols-outlined text-xs">trending_up</span>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 max-w-7xl mx-auto px-6 md:px-10">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mb-2">How RoomNest Works</h2>
          <p className="text-sm text-on-surface-variant">Four simple steps to your new front door.</p>
        </div>
        <div className="relative flex flex-col md:flex-row justify-between items-center gap-8">
          {[
            { step: "1", title: "Search & Discover", desc: "Browse thousands of verified listings with immersive details.", icon: "search" },
            { step: "2", title: "Schedule Visit", desc: "Book a virtual or physical visit with a single click at your convenience.", icon: "event_available" },
            { step: "3", title: "E-Documentation", desc: "Sign rental agreements and complete KYC digitally from home.", icon: "description" },
            { step: "4", title: "Collect Keys", desc: "Move in and enjoy your new lifestyle. We've got the rest covered.", icon: "key", isLast: true }
          ].map((item, idx) => (
            <div key={idx} className="flex-1 text-center relative w-full">
              <div className={`w-20 h-20 ${item.isLast ? 'bg-primary-container text-white' : 'bg-surface-container text-primary'} rounded-full flex items-center justify-center mx-auto mb-6 border-4 border-white shadow-lg z-10 relative`}>
                <span className="material-symbols-outlined text-3xl">{item.icon}</span>
              </div>
              <h4 className="text-sm font-bold mb-2">{item.title}</h4>
              <p className="text-xs text-on-surface-variant px-4">{item.desc}</p>
              {!item.isLast && (
                <div className="hidden md:block absolute top-10 left-[70%] w-full h-[2px] bg-outline-variant/30 -z-0"></div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-surface-container-low border-t border-outline-variant/30">
        <div className="max-w-7xl mx-auto px-6 md:px-10">
          <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface text-center mb-12">Hear from Our Residents</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex gap-0.5 text-secondary-container mb-4">
                {[1, 2, 3, 4, 5].map((n) => <Star key={n} className="w-4 h-4 fill-secondary-container text-transparent" />)}
              </div>
              <p className="text-xs font-semibold text-on-surface italic mb-6">
                &quot;Found a beautiful 2BHK in Indiranagar in just 2 days. The e-agreement signature process was so smooth and easy.&quot;
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-surface-container" />
                <div>
                  <h5 className="text-xs font-bold">Ananya Sharma</h5>
                  <p className="text-[10px] text-on-surface-variant mt-0.5">Marketing Professional</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex gap-0.5 text-secondary-container mb-4">
                {[1, 2, 3, 4, 5].map((n) => <Star key={n} className="w-4 h-4 fill-secondary-container text-transparent" />)}
              </div>
              <p className="text-xs font-semibold text-on-surface italic mb-6">
                &quot;Highly recommend RoomNest for PG rooms. I verified the curfew times and food choices on the site and booked it instantly.&quot;
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-surface-container" />
                <div>
                  <h5 className="text-xs font-bold">Rahul Varma</h5>
                  <p className="text-[10px] text-on-surface-variant mt-0.5">Student, IIT Bombay</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-outline-variant/30">
              <div className="flex gap-0.5 text-secondary-container mb-4">
                {[1, 2, 3, 4, 5].map((n) => <Star key={n} className="w-4 h-4 fill-secondary-container text-transparent" />)}
              </div>
              <p className="text-xs font-semibold text-on-surface italic mb-6">
                &quot;As a property owner, managing listings and tracking visitor leads is extremely transparent. Direct whatsapp button is great.&quot;
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-surface-container" />
                <div>
                  <h5 className="text-xs font-bold">Sanjay K.</h5>
                  <p className="text-[10px] text-on-surface-variant mt-0.5">Property Owner</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA & App Section */}
      <section className="py-20 max-w-7xl mx-auto px-6 md:px-10">
        <div className="bg-primary-container rounded-3xl p-12 flex flex-col md:flex-row items-center justify-between text-white relative overflow-hidden">
          <div className="md:w-1/2 z-10">
            <h2 className="text-3xl md:text-5xl font-extrabold font-plus-jakarta mb-6 leading-tight">Ready to Find Your Next Home?</h2>
            <p className="text-base text-white/80 mb-8">Download our mobile app for exclusive listings and real-time alerts. Your perfect room is just a tap away.</p>
            <div className="flex flex-wrap gap-4 mb-8">
              <a className="bg-on-surface text-white px-6 py-3 rounded-xl flex items-center gap-3 hover:bg-black transition-all cursor-pointer" href="#">
                <span className="material-symbols-outlined">play_books</span>
                <div className="text-left">
                  <p className="text-[9px] uppercase font-bold tracking-widest leading-none">Get it on</p>
                  <p className="text-base font-bold leading-none mt-1">Google Play</p>
                </div>
              </a>
              <a className="bg-on-surface text-white px-6 py-3 rounded-xl flex items-center gap-3 hover:bg-black transition-all cursor-pointer" href="#">
                <span className="material-symbols-outlined">apps</span>
                <div className="text-left">
                  <p className="text-[9px] uppercase font-bold tracking-widest leading-none">Download on the</p>
                  <p className="text-base font-bold leading-none mt-1">App Store</p>
                </div>
              </a>
            </div>
            <p className="text-xs font-bold uppercase tracking-widest opacity-60">Join 1,000,000+ happy renters today</p>
          </div>
          <div className="md:w-1/2 mt-12 md:mt-0 relative flex justify-center">
            {/* Phone Mockup */}
            <div className="w-56 h-[400px] bg-on-surface border-4 border-on-surface-variant rounded-[32px] relative shadow-2xl z-10 overflow-hidden transform rotate-12 md:translate-x-12">
              <div className="absolute inset-0 bg-white p-4 flex flex-col justify-between">
                <div className="w-full h-6 bg-surface-container rounded-full mb-3"></div>
                <div className="w-full h-32 bg-surface-container-high rounded-xl mb-3"></div>
                <div className="space-y-1.5">
                  <div className="w-full h-3 bg-surface-container rounded-full"></div>
                  <div className="w-2/3 h-3 bg-surface-container rounded-full"></div>
                </div>
                <div className="w-full h-8 bg-primary rounded-lg"></div>
              </div>
            </div>
            <div className="w-56 h-[400px] bg-on-surface border-4 border-on-surface-variant rounded-[32px] absolute shadow-2xl overflow-hidden -translate-x-16 translate-y-8 scale-90 opacity-50"></div>
          </div>
          <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
        </div>
      </section>
    </div>
  );
}
