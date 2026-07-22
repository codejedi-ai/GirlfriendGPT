import { Outlet } from "react-router-dom";
import { Navbar } from "@components/navbar";
import { Footer } from "@/components/footer";

export function Layout() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen flex flex-col pt-16">
        <Outlet />
      </main>
      <Footer />
    </>
  );
}
