import "./css/nav.scss"
import "./css/App.css"

export default function Navbar(){
    return (
        <nav className="nav">
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@40,200,0,-25" />
            <a href="/">
                <span className="material-symbols-outlined">
                    home
                </span>Home
                </a>
            <ul>
                <li>
                    <a href="/transfer">
                    <span className="material-symbols-outlined">
                        paid
                    </span>
                        Trasferisci denaro
                    </a>
                </li>
                <li> 
                    <a href="/test">Test</a>
                </li>    
            </ul>
        </nav>
    )
}
