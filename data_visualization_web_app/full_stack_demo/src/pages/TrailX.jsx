import React, { useEffect, useState } from 'react';
import { db, storage } from '../firebase-config';
import { ref, getDownloadURL } from 'firebase/storage';
import { collection, doc, getDocs, getDoc } from "firebase/firestore";

// Import icons.
import { BsFillCircleFill } from "react-icons/bs";
import { IoIosMore } from 'react-icons/io';

// Import components.
import { DropDownListComponent } from '@syncfusion/ej2-react-dropdowns';
import { LineChart } from '../components';

// Import the data for the main page.
import { medicalproBranding, recentTransactions, weeklyStats, dropdownData, SparklineAreaData, ecomPieChartData } from '../data/dummy';
import { weeklySparklineAreaData } from '../data/weekly-analysis'

// Import the current states.
import { useStateContext } from '../contexts/ContextProvider';

const fetchIssues = async () => {
    const issuesCollectionRef = collection(db, 'feedbacks'); // 'issues' is the name of the Firestore collection
    const data = await getDocs(issuesCollectionRef);
    return data.docs.map((doc) => ({ ...doc.data(), id: doc.id }));
};

const DropDown = ({ currentMode }) => (
    <div className="w-28 border-1 border-color px-2 py-1 rounded-md">
        <DropDownListComponent id="time" fields={{ text: 'Time', value: 'Id' }} style={{ border: 'none', color: (currentMode === 'Dark') && 'white' }} value="1" dataSource={dropdownData} popupHeight="220px" popupWidth="120px" />
    </div>
);

const TrailX = () => {
    const [issues, setIssues] = useState([]);
    const { currentColor, currentMode } = useStateContext();
    const [dailyData, setDailyData] = useState({
        "Total User Count": "Loading...",
        "Pedestrians": "Loading...",
        "Cyclists": "Loading...",
        "Dog Walkers": "Loading...",
        "lastUpdated": "Loading..."
    });

    useEffect(() => {
        const getIssues = async () => {
            const issuesData = await fetchIssues();
            setIssues(issuesData);
        };

        getIssues();
    }, []);
    useEffect(() => {
        const fetchData = async () => {
            const now = new Date();
            const utc8Time = new Date(now.getTime() - (8 * 60 * 60 * 1000));
            const year = utc8Time.getUTCFullYear();
            const month = utc8Time.getUTCMonth() + 1;
            const day = utc8Time.getUTCDate();
            const todayString = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;

            const docRef = doc(db, "daily_user_counts", todayString);
            const docSnap = await getDoc(docRef);

            if (docSnap.exists()) {
                const data = docSnap.data();
                setDailyData({
                    "Total User Count": data["Total User Count"] || "0",
                    "Pedestrians": data["Pedestrians"] || "0",
                    "Cyclists": data["Cyclists"] || "0",
                    "Dog Walkers": data["Dog Walkers"] || "0",
                    "lastUpdated": data["lastUpdated"] ? new Date(data["lastUpdated"].toDate()).toLocaleString() : "Not available"
                });
            } else {
                console.log("No such document!");
                setDailyData({
                    "Total User Count": "0",
                    "Pedestrians": "0",
                    "Cyclists": "0",
                    "Dog Walkers": "0",
                    "lastUpdated": "Not available"
                });
            }
        };

        fetchData();
    }, []);

    const [gcsData, setGcsData] = useState(null);

    const fetchDataFromFirestore = async () => {
        try {
            const querySnapshot = await getDocs(collection(db, "user_counter_output"));
            const data = querySnapshot.docs.map(doc => doc.data());
            setGcsData(data); // Assuming you have a state called gcsData to store the fetched data
        } catch (error) {
            console.error("Could not fetch data from Firestore:", error);
        }
    };

    // Using useEffect to call fetchDataFromFirestore when the component mounts
    useEffect(() => {
        fetchDataFromFirestore();
    }, []);
    const sortedIssues = issues.sort((a, b) => {
        // Assuming createdAt is a Firebase Timestamp, convert to Date objects
        const dateA = a.createdAt.toDate();
        const dateB = b.createdAt.toDate();
    
        return dateB - dateA; // For ascending order, swap dateA and dateB for descending
      });



    return (
        <div className='mt-12'>
            <div className="w-full flex items-center justify-between px-2 h-12">
                <img className="max-w-xs" alt="Vector" src="/Vector17.svg" style={{ flexShrink: 0 }} />
                <div className="text-center text-black font-semibold text-2xl flex-1">
                    DASHBOARD
                </div>
                <img className="max-w-xs" alt="Vector" src="/Vector18.svg" style={{ flexShrink: 0 }} />
            </div>


            {/* To render the general layout for the hero and the card layouts. */}
            <div className='flex flex-wrap lg:flex-nowrap justify-center'>
                {/* To render the hero layout of the main page. */}
                <div className='h-44 w-full lg:w-80 p-8 pt-9 m-3
                rounded-xl bg-none bg-no-repeat bg-cover bg-center
                bg-white dark:text-gray-200 dark:bg-secondary-dark-bg'>
                    {/* To render the text in the hero section. */}
                    <div className='flex justify-between items-center'>
                        <div>
                            <p className='font-bold text-gray-400'>
                                Today
                            </p>
                            <p className='text-2xl'>
                                {dailyData ? dailyData["Total User Count"] : "Loading..."} users
                            </p>
                            <span className='p-1.5 hover:drop-shadow-xl cursor-pointer rounded-full text-white bg-[#01BDAE] text-xs'>
                                {/* Example or calculated value */}
                                66%
                            </span>
                            <div>Last Updated: {dailyData.lastUpdated}</div>
                        </div>
                    </div>
                </div>
                {/* To render the card layout of the main page. */}
                <div className='flex flex-wrap m-3 gap-3 justify-center items-center'>
                    {gcsData ? (
                        <>
                            <div
                                className='p-4 pt-9 md:w-56 rounded-2xl bg-white dark:text-gray-200 dark:bg-secondary-dark-bg'
                            >
                                <p className='text-2xl opacity-90 rounded-full hover:drop-shadow-xl'>
                                    🚶‍♂️ Pedestrians
                                </p>
                                <p className='mt-3 text-lg font-semibold'>
                                    {dailyData ? dailyData["Pedestrians"] : "Loading..."}
                                </p>
                            </div>

                            <div
                                className='p-4 pt-9 md:w-56 rounded-2xl bg-white dark:text-gray-200 dark:bg-secondary-dark-bg'
                            >
                                <p className='text-2xl opacity-90 rounded-full hover:drop-shadow-xl'>
                                    🚴 Cyclists
                                </p>
                                <p className='mt-3 text-lg font-semibold'>
                                    {dailyData ? dailyData["Cyclists"] : "Loading..."}
                                </p>
                            </div>

                            <div
                                className='p-4 pt-9 md:w-56 rounded-2xl bg-white dark:text-gray-200 dark:bg-secondary-dark-bg'
                            >
                                <p className='text-2xl opacity-90 rounded-full hover:drop-shadow-xl'>
                                    🐕 Dog Walkers
                                </p>
                                <p className='mt-3 text-lg font-semibold'>
                                    {dailyData ? dailyData["Dog Walkers"] : "Loading..."}
                                </p>
                            </div>
                        </>
                    ) : (
                        <p>Loading data...</p>
                    )}
                </div>
            </div>
            {/* To render a big card layout for the syncfusion data visualization component. */}

            <div className='flex gap-3 flex-wrap justify-center'>
                <div className="flex gap-10 m-4 flex-wrap justify-center bg-white dark:text-gray-200 dark:bg-secondary-dark-bg p-6 rounded-2xl w-96 md:w-760">
                    <div className='flex justify-between p-4'>
                        <p className='text-xl font-semibold'>Trend Summary</p>
                    </div>
                    <div className="md:w-full overflow-auto">
                        <LineChart />
                    </div>
                </div>

                <div className="overflow-x-auto relative shadow-md sm:rounded-lg">
                    <table className="w-full text-sm text-left text-gray-500 dark:text-gray-400">
                        <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
                            <tr>
                                <th scope="col" className="py-3 px-6">Created At</th>
                                <th scope="col" className="py-3 px-6">Email</th>
                                <th scope="col" className="py-3 px-6">Issue Description</th>
                                <th scope="col" className="py-3 px-6">Location</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedIssues.map((issue) => (
                                <tr key={issue.id} className="bg-white border-b dark:bg-gray-800 dark:border-gray-700">
                                    <td className="py-4 px-6">
                                        {issue.createdAt.toDate().toLocaleString()} {/* Adjust formatting as needed */}
                                    </td>
                                    <td className="py-4 px-6">{issue.email}</td>
                                    <td className="py-4 px-6">{issue.issueDescription}</td>
                                    <td className="py-4 px-6">{issue.location}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div >
    );
};

export default TrailX

