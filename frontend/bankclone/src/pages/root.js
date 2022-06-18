import React from "react";
import { useState } from "react";
import "../css/home.scss"
import { Input } from "reakit/Input";
import { useTabState, Tab, TabList, TabPanel } from "reakit/Tab";
import { useToolbarState } from "reakit";
import axios from "axios"

export default function Root(){
    const toolbar = useToolbarState({ loop: true });
    let [accountId, setAccountId] = useState("");
    let [fetchedData, setFetchedData] = useState(false);
    let fetchData
    let [userInfo, setUserInfo] = useState([]);
    let [transactions, setTransactions] = useState([]);
    let [withdraws, setWithdraws] = useState([]);

    function UserTable(){
        return(
            <table>
                <tbody>
                    <tr>
                        <th>Account Id</th>
                        <th>Name</th>
                        <th>Surname</th>
                        <th>Balance</th>
                        <th>Registration Date</th>
                    </tr>
                    <tr>
                    {Object.keys(userInfo).map((keyName, i) => (
                        <td >{userInfo[keyName]}</td>
                    ))}
                    </tr>
                </tbody>
            </table>
        )
    }

    function TransactionsTable(){
        return(
            <table>
                <tbody>
                    <tr>
                        <th>Sender Id</th>
                        <th>Receiver Id</th>
                        <th>Transaction Id</th>
                        <th>Amount</th>
                        <th>Transaction Date</th>
                    </tr>
                    {transactions.map((item, i) => (
                        <tr key={i}>
                            <td>{item.sender}</td>
                            <td>{item["receiver"]}</td>
                            <td>{item['transactionId']}</td>
                            <td>{item['amount']}</td>
                            <td>{item['transactionDate']}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        )
    }

    function Toolbarr(){
        const tab = useTabState();
        return(
            <>
            <TabList {...tab} aria-label="My tabs" className="tab-list">
                <Tab {...tab}>Informazioni utente</Tab>
                <Tab {...tab}>Lista Transazioni</Tab>
                <Tab {...tab}>Lista Prelievi/Depositi</Tab>
            </TabList>
            <TabPanel {...tab}><UserTable/></TabPanel>
            <TabPanel {...tab}><TransactionsTable/></TabPanel>
            <TabPanel {...tab}>Tab 3</TabPanel>
            </>
        )
    }

    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId: 'Fetch POST Request Example' })
    };

    function fetch_user(){
        if(accountId != 0){
            //let res = await fetch('http://localhost:8000/api/account/' + accountId)

            axios.get('http://localhost:8000/api/account/' + accountId)
            .then(res => {
                const persons = res.data;
                setTransactions(persons[1]['transactions'])
                setUserInfo(persons[0]['user_info'])
                setWithdraws(persons[2]["withdraws"])
                setFetchedData(true);
            })
            /*
            let data = await res.json()
            setFetchData(data)
            setFetchedData(true);
            await console.log(fetchData[0]['user_info'])
            /*
            setUserInfo(fetchData[0]['user_info'])
            setTransactions(fetchData[1]["transactions"])
            setWithdraws(fetchData[2]["withdraws"])
        */}
    }

    function reset_data(){

    }

    return(
        <div id="home">
            <div className="ricerca-text">
                <h2>Ricerca utente</h2>
                <span className="material-symbols-outlined">
                close
                </span>
            </div>
            <form className="ricerca-input" >
                <Input placeholder="Cerca un utente nel database" id="ricerca-input" value={accountId} onChange = {e => setAccountId(e.target.value)}/>
                <input type="button" onClick={fetch_user} id="ricerca-button" value="Cerca"/>
            </form>
            {fetchedData && <Toolbarr/>
            }
        </div>
    )
}