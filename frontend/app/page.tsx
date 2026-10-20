"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Welcome } from "../components/welcome";
import Dashboard from "../components/dashboard";
export default function Home(){
 const router=useRouter();
 const [access,setAccess]=useState<"login"|"register"|null>(null);
 if(access)return <Dashboard initialAuthOpen initialRegister={access==="register"}/>;
 return <Welcome onLogin={()=>setAccess("login")} onRegister={()=>setAccess("register")} onExplore={()=>router.push("/resumen")}/>;
}
