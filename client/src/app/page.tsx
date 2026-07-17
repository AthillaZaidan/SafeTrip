"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Cctv, TriangleAlert, FileSearch, ArrowRight } from "lucide-react";

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <div className="flex min-h-screen flex-col bg-cloud">
      <nav className="flex items-center justify-between bg-white border-b border-hairline px-6 py-4 lg:px-12">
        <div className="flex items-center gap-4">
          <span className="text-xl font-extrabold tracking-tight text-primary">
            Safe Trip
          </span>
        </div>
        <div className="hidden items-center gap-8 md:flex">
          <Link href="#features" className="text-sm font-medium text-muted hover:text-ink">
            Platform
          </Link>
          <Link href="#how-it-works" className="text-sm font-medium text-muted hover:text-ink">
            Solutions
          </Link>
          <Link
            href="/login"
            className="rounded-full bg-primary px-6 py-2.5 text-sm font-bold text-white transition-colors hover:bg-primary-active"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col justify-center bg-cloud px-6 py-20 lg:px-12">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="mb-6 inline-block rounded-full bg-surface-strong px-4 py-1.5 text-sm font-bold text-ink border border-hairline shadow-sm">
              <span className="mr-2 inline-block h-2 w-2 rounded-full bg-signal animate-pulse" />
              Live Detection Active
            </span>
            <h1 className="mb-6 text-5xl font-extrabold leading-tight tracking-tight text-ink md:text-6xl lg:text-7xl">
              Transit Safety, <br />
              Powered by Vision AI
            </h1>
            <p className="mx-auto mb-10 max-w-2xl text-lg text-muted md:text-xl">
              Safe Trip transforms ordinary CCTV feeds into active incident detection systems, 
              connecting passengers and control rooms in seconds.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/login"
                className="group flex w-full items-center justify-center gap-2 rounded-full bg-primary px-8 py-4 text-base font-bold text-white transition-colors hover:bg-primary-active sm:w-auto"
              >
                Go to Dashboard
                <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          </motion.div>
        </div>

        {/* Feature Highlights */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="mx-auto mt-24 grid max-w-5xl gap-5 md:grid-cols-3"
        >
          {[
            {
              icon: <Cctv className="h-6 w-6 text-navy" />,
              title: "Live Detection",
              desc: "Detect risk events from CCTV footage instantly with contextual alerts and risk scores.",
            },
            {
              icon: <TriangleAlert className="h-6 w-6 text-alert" />,
              title: "Rapid Response",
              desc: "Dispatch the nearest field officer with approved playbook recommendations.",
            },
            {
              icon: <FileSearch className="h-6 w-6 text-teal" />,
              title: "VLM Investigation",
              desc: "Retrieve critical evidence using natural-language incident reports.",
            },
          ].map((feat, idx) => (
            <motion.div
              key={idx}
              variants={itemVariants}
              className="flex flex-col items-center rounded-2xl bg-white p-6 text-center shadow-[0_1px_6px_rgba(16,24,40,0.06)]"
            >
              <div className="mb-4 rounded-xl bg-cloud p-3">{feat.icon}</div>
              <h3 className="mb-2 text-lg font-bold text-ink">{feat.title}</h3>
              <p className="text-sm leading-relaxed text-muted">{feat.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </main>
    </div>
  );
}
