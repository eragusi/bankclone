import React from "react";
import "./css/App.css"
import Navbar from "./navbar";
import Transfer from "./pages/transfer";
import Test from "./pages/test";
import Root from "./pages/root";

function App() {
  let Component
  switch (window.location.pathname){
    case "/":
      Component = Root  
      break

    case "/transfer":
      Component = Transfer; 
      break

    case "/test":
      Component = Test;
      break

    default:
      Component = Root
      break
  }
  return (
    <div className="App">
      <Navbar/>
      <Component/>
    </div>
  );
}

export default App;
