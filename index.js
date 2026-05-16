import {initializeApp} from 'firebase/app';
import {getAuth} from 'firebase/auth';
import {getFirestore,collection, getDocs} from 'firebase/firestore';

const firebaseapp = initializeApp({
  apiKey: "AIzaSyC9n8sXo2l3m1e5v6w7x8y9z0a1b2c3d4",
  authDomain: "gdg-ipl-guessing-game.firebaseapp.com",
  projectId: "gdg-ipl-guessing-game",
  storageBucket: "gdg-ipl-guessing-game.appspot.com",
  appId: "1:1234567890:web:abcdef123456",
  mesaurementId: "G-1A2B3C4D5E"});

const auth = getAuth(firebaseapp);
const db = getFirestore(firebaseapp);
const players_collection = collection(db,'players');


onauthStateChanged(auth, (user) => {
  if (user) {
    console.log("User signed in:", user);}
        else{
    console.log("No user signed in.");
        }
    });

    