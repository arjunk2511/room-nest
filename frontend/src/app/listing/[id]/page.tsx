"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { getAuthHeader } from "@/lib/supabase";
import { 
  MapPin, Phone, ShieldCheck, Heart, Share2, Star, Calendar, 
  MessageSquare, Users, Eye, PhoneCall, ChevronRight, HelpCircle
} from "lucide-react";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ListingDetailsPage({ params }: PageProps) {
  const router = useRouter();
  const { id } = use(params);

  const [listing, setListing] = useState<any>(null);
  const [landmarks, setLandmarks] = useState<any>(null);
  const [activeTab, setActiveTab] = useState("schools");
  const [loading, setLoading] = useState(true);
  const [landmarkLoading, setLandmarkLoading] = useState(false);

  // Review Form State
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [reviewError, setReviewError] = useState("");
  const [reviewSuccess, setReviewSuccess] = useState("");

  const fetchListing = () => {
    setLoading(true);
    fetch(`/api/listings/${id}/`)
      .then((res) => res.json())
      .then((data) => {
        if (data && !data.error) {
          setListing(data);
          // Fetch landmarks
          fetchLandmarks(data.id);
        } else {
          router.push("/404");
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading listing details:", err);
        setLoading(false);
      });
  };

  const fetchLandmarks = (listingId: number) => {
    setLandmarkLoading(true);
    fetch(`/api/listing/${listingId}/landmarks/`)
      .then((res) => res.json())
      .then((data) => {
        setLandmarks(data);
        setLandmarkLoading(false);
      })
      .catch((err) => {
        console.error("Error loading landmarks:", err);
        setLandmarkLoading(false);
      });
  };

  useEffect(() => {
    fetchListing();
  }, [id]);

  const handleTrackClick = (type: "Call" | "WhatsApp") => {
    fetch(`/api/listings/${id}/track-click/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type })
    }).then(() => {
      // Re-fetch detail to increment lead counts if needed
      fetch(`/api/listings/${id}/`).then(res => res.json()).then(data => {
        if (data && !data.error) setListing(data);
      });
    });
  };

  const handleToggleWishlist = async () => {
    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    fetch(`/api/listings/${id}/toggle-wishlist/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": authHeader
      }
    }).then((res) => res.json()).then((data) => {
      if (data.status === "success") {
        alert(data.saved ? "Added to Wishlist!" : "Removed from Wishlist!");
      }
    });
  };

  const handlePostReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setReviewError("");
    setReviewSuccess("");

    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    fetch(`/api/listing/${id}/review/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader
      },
      body: JSON.stringify({ rating, comment })
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          setReviewError(data.error);
        } else {
          setReviewSuccess("Review submitted successfully!");
          setComment("");
          fetchListing(); // Reload reviews list
        }
      })
      .catch((err) => {
        setReviewError("Failed to submit review.");
      });
  };

  if (loading) {
    return <div className="p-12 text-center animate-pulse font-semibold">Loading listing details...</div>;
  }

  if (!listing) {
    return <div className="p-12 text-center text-error font-semibold">Listing not found.</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 w-full flex-1 flex flex-col">
      {/* Breadcrumb / Top Info */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <span className="text-xs text-on-surface-variant font-semibold">
            Properties / {listing.city?.name || 'Mysore'} / {listing.area?.name || listing.location}
          </span>
          <h1 className="text-xl md:text-2xl font-extrabold font-plus-jakarta text-on-surface mt-1">{listing.title}</h1>
        </div>
        <div className="flex gap-2">
          <button onClick={handleToggleWishlist} className="p-2 border border-outline-variant rounded-xl hover:bg-surface-container transition-colors">
            <Heart className="w-5 h-5 text-on-surface-variant" />
          </button>
          <button className="p-2 border border-outline-variant rounded-xl hover:bg-surface-container transition-colors">
            <Share2 className="w-5 h-5 text-on-surface-variant" />
          </button>
        </div>
      </div>

      {/* Image Gallery */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="md:col-span-2 relative h-80 md:h-[420px] rounded-2xl overflow-hidden shadow-sm">
          {listing.image ? (
            <img src={listing.image} alt={listing.title} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-surface-container-high flex items-center justify-center text-5xl">🏢</div>
          )}
          {listing.is_verified && (
            <div className="absolute top-4 right-4 bg-white/90 backdrop-blur text-primary px-3.5 py-1 rounded-full text-xs font-bold flex items-center gap-1 shadow-md">
              <ShieldCheck className="w-4 h-4 fill-primary text-white" /> Verified Listing
            </div>
          )}
        </div>
        <div className="hidden md:grid grid-rows-2 gap-4 h-[420px]">
          {listing.gallery && listing.gallery.slice(0, 2).map((imgUrl: string, idx: number) => (
            <div key={idx} className="relative rounded-2xl overflow-hidden h-[202px] bg-surface-container-high shadow-sm">
              <img src={imgUrl} alt={`gallery-${idx}`} className="w-full h-full object-cover" />
            </div>
          ))}
          {(!listing.gallery || listing.gallery.length === 0) && (
            <div className="row-span-2 rounded-2xl bg-surface-container-low border border-dashed border-outline-variant flex items-center justify-center text-xs font-semibold text-text-muted">
              No Additional Photos
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Key Parameters */}
          <div className="bg-white border border-outline-variant rounded-2xl p-6 grid grid-cols-3 gap-4 shadow-sm text-center">
            <div>
              <div className="text-[10px] font-bold text-outline uppercase tracking-wider">Stay Type</div>
              <div className="text-sm font-extrabold text-on-surface mt-1">{listing.type}</div>
            </div>
            <div className="border-l border-r border-outline-variant/50">
              <div className="text-[10px] font-bold text-outline uppercase tracking-wider">Rent / Month</div>
              <div className="text-sm font-extrabold text-primary mt-1">₹{parseFloat(listing.price).toLocaleString('en-IN')}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-outline uppercase tracking-wider">Security Deposit</div>
              <div className="text-sm font-extrabold text-on-surface mt-1">₹{parseFloat(listing.deposit).toLocaleString('en-IN')}</div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-md font-bold text-on-surface mb-3">Property Description</h3>
            <p className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-line">{listing.description}</p>
          </div>

          {/* Amenities Badges */}
          <div>
            <h3 className="text-md font-bold text-on-surface mb-3">Facilities</h3>
            <div className="flex flex-wrap gap-2">
              {listing.facilities && listing.facilities.map((fac: string, idx: number) => (
                <span key={idx} className="px-4 py-2 bg-surface-container text-xs font-bold text-on-surface rounded-full">
                  {fac}
                </span>
              ))}
            </div>
          </div>

          {/* House Rules */}
          <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-on-surface mb-4">House Rules & Preferences</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
              <div className="p-3 bg-surface-container-low rounded-xl">
                <div className="text-[10px] font-bold text-outline uppercase">Food Preference</div>
                <div className="text-xs font-bold text-on-surface mt-1">{listing.food_preference}</div>
              </div>
              <div className="p-3 bg-surface-container-low rounded-xl">
                <div className="text-[10px] font-bold text-outline uppercase">Curfew Hours</div>
                <div className="text-xs font-bold text-on-surface mt-1">{listing.curfew}</div>
              </div>
              <div className="p-3 bg-surface-container-low rounded-xl">
                <div className="text-[10px] font-bold text-outline uppercase">Visitor Access</div>
                <div className="text-xs font-bold text-on-surface mt-1">{listing.visitors}</div>
              </div>
            </div>
          </div>

          {/* Tabbed Neighborhood Discovery */}
          <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-on-surface mb-2">Explore the Neighborhood</h3>
            <p className="text-xs text-on-surface-variant mb-6">Discover drive and walk times to critical spots nearby.</p>

            {landmarkLoading ? (
              <div className="py-8 text-center animate-pulse text-xs text-text-muted">Discovering neighborhood details...</div>
            ) : landmarks ? (
              <div>
                {/* Tabs Selector */}
                <div className="flex gap-2 border-b border-outline-variant/30 pb-3 mb-6 overflow-x-auto">
                  {Object.keys(landmarks).map((key) => (
                    <button
                      key={key}
                      onClick={() => setActiveTab(key)}
                      className={`px-4 py-1.5 rounded-full text-xs font-bold shrink-0 transition-colors ${
                        activeTab === key ? "bg-primary text-white" : "bg-surface-container hover:bg-outline-variant/30 text-on-surface-variant"
                      }`}
                    >
                      {key.charAt(0).toUpperCase() + key.slice(1).replace("_", " ")}
                    </button>
                  ))}
                </div>

                {/* Tab Content */}
                <div className="space-y-4">
                  {landmarks[activeTab] && landmarks[activeTab].length > 0 ? (
                    landmarks[activeTab].map((l: any, idx: number) => (
                      <div key={idx} className="flex justify-between items-center bg-surface-container-low p-4 rounded-xl">
                        <div className="flex items-center gap-3">
                          <span className="text-lg">{l.icon || "📍"}</span>
                          <div>
                            <h4 className="text-xs font-bold text-on-surface">{l.name}</h4>
                            <p className="text-[10px] text-on-surface-variant mt-0.5">{l.distance}</p>
                          </div>
                        </div>
                        <div className="text-right text-[10px] font-semibold text-text-muted">
                          <div>{l.drive_time}</div>
                          <div className="mt-0.5">{l.walk_time}</div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-6 text-xs text-text-muted font-medium">No nearby landmarks found for this category.</div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-xs text-text-muted">No neighborhood insights available.</div>
            )}
          </div>

          {/* Reviews List & Post Form */}
          <div className="space-y-6">
            <h3 className="text-md font-bold text-on-surface">Reviews ({listing.reviews?.length || 0})</h3>
            
            <div className="space-y-4">
              {listing.reviews && listing.reviews.map((r: any) => (
                <div key={r.id} className="bg-white border border-outline-variant rounded-2xl p-5 shadow-sm">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h5 className="text-xs font-bold">{r.user.first_name || r.user.username}</h5>
                      <span className="text-[10px] text-on-surface-variant mt-0.5 block">{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex gap-0.5 text-secondary-container">
                      {Array.from({ length: r.rating }).map((_, idx) => (
                        <Star key={idx} className="w-3.5 h-3.5 fill-secondary-container text-transparent" />
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-on-surface leading-relaxed">{r.comment}</p>
                </div>
              ))}
            </div>

            {/* Post Review Form */}
            <form onSubmit={handlePostReview} className="bg-white border border-outline-variant rounded-2xl p-6 shadow-sm space-y-4">
              <h4 className="text-sm font-bold text-on-surface">Write a Review</h4>
              
              <div>
                <label className="block text-xs font-semibold text-on-surface-variant mb-2">Rating</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((num) => (
                    <button
                      type="button"
                      key={num}
                      onClick={() => setRating(num)}
                      className={`w-8 h-8 rounded-lg border text-xs font-bold transition-all ${
                        rating === num ? "bg-primary text-white border-primary" : "border-outline-variant hover:bg-surface-container"
                      }`}
                    >
                      {num}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-on-surface-variant mb-2">Comments</label>
                <textarea
                  rows={4}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share your stay experience or thoughts..."
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                />
              </div>

              {reviewError && <p className="text-xs text-error font-medium">{reviewError}</p>}
              {reviewSuccess && <p className="text-xs text-primary font-medium">{reviewSuccess}</p>}

              <button type="submit" className="px-6 py-2.5 bg-primary text-white rounded-xl text-xs font-bold hover:opacity-90 active:scale-95 transition-all">
                Submit Review
              </button>
            </form>
          </div>
        </div>

        {/* Sidebar Actions */}
        <aside className="space-y-6">
          {/* Action Card */}
          <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-md sticky top-20">
            <div className="flex justify-between items-center pb-4 border-b border-outline-variant/30 mb-6">
              <div>
                <span className="text-[10px] text-on-surface-variant font-semibold">Rent Amount</span>
                <div className="text-lg font-extrabold text-primary mt-0.5">₹{parseFloat(listing.price).toLocaleString('en-IN')}<span className="text-xs font-normal text-on-surface-variant">/mo</span></div>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-on-surface-variant font-semibold">Deposit</span>
                <div className="text-xs font-bold text-on-surface mt-0.5">₹{parseFloat(listing.deposit).toLocaleString('en-IN')}</div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3 text-xs text-on-surface">
                <Calendar className="w-4 h-4 text-primary shrink-0" />
                <span>Available from: <strong>{listing.available_from}</strong></span>
              </div>
              <div className="flex items-center gap-3 text-xs text-on-surface">
                <Eye className="w-4 h-4 text-primary shrink-0" />
                <span>Property views: <strong>{listing.views_count}</strong></span>
              </div>
              {listing.phone && (
                <div className="flex items-center gap-3 text-xs text-on-surface">
                  <Phone className="w-4 h-4 text-primary shrink-0" />
                  <span>Contact: <strong>{listing.phone}</strong></span>
                </div>
              )}
            </div>

            <div className="mt-8 space-y-3">
              {listing.phone && (
                <a
                  href={`tel:${listing.phone}`}
                  onClick={() => handleTrackClick("Call")}
                  className="w-full py-3 bg-primary text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-primary/10"
                >
                  <PhoneCall className="w-4 h-4" /> Call Owner
                </a>
              )}
              {listing.phone && (
                <a
                  href={`https://wa.me/91${listing.phone}?text=Hi, I am interested in your RoomNest listing: ${listing.title}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => handleTrackClick("WhatsApp")}
                  className="w-full py-3 bg-secondary-container text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-secondary-container/10"
                >
                  <MessageSquare className="w-4 h-4" /> WhatsApp Chat
                </a>
              )}

              {listing.exact_location && (
                <a
                  href={listing.exact_location}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full py-3 bg-surface-container hover:bg-outline-variant/30 text-on-surface rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all"
                >
                  <MapPin className="w-4 h-4 text-primary" /> View on Maps
                </a>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
