"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Calendar, Tag, MapPin, ShieldCheck, ArrowLeft, ArrowRight } from "lucide-react";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default function BlogDetailPage({ params }: PageProps) {
  const router = useRouter();
  const { slug } = use(params);

  const [post, setPost] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/blogs/${slug}/`)
      .then((res) => res.json())
      .then((data) => {
        if (data && !data.error) {
          setPost(data);
          // Set custom browser document title for SEO
          if (typeof window !== "undefined") {
            document.title = data.seo_title || data.title;
          }
        } else {
          router.push("/blog");
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error loading blog details:", err);
        setLoading(false);
      });
  }, [slug]);

  if (loading) {
    return <div className="p-12 text-center animate-pulse font-semibold">Loading article details...</div>;
  }

  if (!post) {
    return <div className="p-12 text-center text-error font-semibold">Article not found.</div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 w-full flex-1 flex flex-col">
      {/* Back button */}
      <Link href="/blog" className="flex items-center gap-1.5 text-xs font-bold text-primary hover:underline mb-6">
        <ArrowLeft className="w-4 h-4" /> Back to Blog
      </Link>

      {/* Header Info */}
      <div className="space-y-4 mb-8">
        <div className="flex items-center gap-4 text-[10px] text-text-muted font-bold">
          <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> {new Date(post.created_at).toLocaleDateString()}</span>
          {post.category && <span className="flex items-center gap-1"><Tag className="w-3.5 h-3.5" /> {post.category}</span>}
        </div>
        <h1 className="text-2xl md:text-4xl font-extrabold font-plus-jakarta text-on-surface leading-tight">{post.title}</h1>
        <p className="text-sm text-on-surface-variant leading-relaxed font-medium">{post.summary}</p>
      </div>

      {/* Main image */}
      {post.image && (
        <div className="h-64 md:h-[400px] w-full rounded-2xl overflow-hidden shadow-sm mb-8 bg-surface-container-high">
          <img src={post.image} alt={post.title} className="w-full h-full object-cover" />
        </div>
      )}

      {/* Content */}
      <article className="prose prose-sm max-w-none text-on-surface leading-relaxed whitespace-pre-line text-xs md:text-sm mb-12">
        {post.content}
      </article>

      {/* Related Listings Section */}
      {post.related_listings && post.related_listings.length > 0 && (
        <div className="border-t border-outline-variant/30 pt-8 mb-12 space-y-6">
          <h3 className="text-md font-bold text-on-surface">Properties Mentioned in this Guide</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {post.related_listings.map((l: any) => (
              <Link href={`/listing/${l.id}`} key={l.id} className="bg-white rounded-2xl overflow-hidden property-card-shadow group border border-outline-variant/30 transition-all duration-300 hover:-translate-y-1">
                <div className="relative h-40 w-full bg-surface-container-high overflow-hidden shrink-0">
                  {l.image ? (
                    <img src={l.image} alt={l.title} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-3xl">🏢</div>
                  )}
                  {l.is_verified && (
                    <div className="absolute top-3 right-3 bg-white/90 backdrop-blur text-primary px-2.5 py-0.5 rounded-full text-[9px] font-bold flex items-center gap-1 shadow-md">
                      <ShieldCheck className="w-3 h-3 fill-primary text-white" /> Verified
                    </div>
                  )}
                </div>
                <div className="p-4">
                  <h4 className="text-xs font-bold text-on-surface line-clamp-1 group-hover:text-primary transition-colors">{l.title}</h4>
                  <div className="text-primary font-bold text-xs mt-1">
                    ₹{parseFloat(l.price).toLocaleString('en-IN')}/mo
                  </div>
                  <p className="text-[10px] text-on-surface-variant flex items-center gap-1 mt-2">
                    <MapPin className="w-3 h-3" /> {l.location}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Related Posts Section */}
      {post.related_posts && post.related_posts.length > 0 && (
        <div className="border-t border-outline-variant/30 pt-8 space-y-6">
          <h3 className="text-md font-bold text-on-surface">Continue Reading</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {post.related_posts.map((rp: any, idx: number) => (
              <Link href={`/blog/${rp.slug}`} key={idx} className="bg-white border border-outline-variant rounded-2xl p-4 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow">
                <div>
                  <h4 className="text-xs font-bold text-on-surface mb-2 line-clamp-2">{rp.title}</h4>
                  <p className="text-[11px] text-on-surface-variant line-clamp-2 leading-relaxed">{rp.summary}</p>
                </div>
                <div className="text-[10px] font-bold text-primary flex items-center gap-1 mt-4">
                  Read Article <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
