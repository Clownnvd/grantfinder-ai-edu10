import type { Metadata } from "next";
import { Be_Vietnam_Pro } from "next/font/google";
import "./globals.css";

const beVietnam=Be_Vietnam_Pro({variable:"--font-be-vietnam",subsets:["latin","vietnamese"],weight:["400","500","600","700"],display:"swap"});
export const metadata:Metadata={title:"GrantFinder AI — tìm quỹ có căn cứ",description:"Trợ lý rà soát cơ hội tài trợ, đối chiếu eligibility và dựng proposal có trích nguồn với human-in-the-loop."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="vi" className={`${beVietnam.variable} h-full`}><body className="min-h-full">{children}</body></html>}
