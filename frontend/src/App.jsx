import { useState, useEffect } from 'react'
import './App.css'
import MP3Tag from 'mp3tag.js';
import axios from "axios";

function App() {
  
  const[link, setLink] = useState("");
  const[process, setProcess] = useState(false);
  const[data, setData] = useState({});
  
  const fetchData = async () => {
    try {
      const res = await axios.get(`https://youtube-to-mp3-converter-56pe.onrender.com//api/retrieve_yt_info`, {
        params: { url: link },
      });

      const data = res.data;
      const genre_list = data.genres?.map(g => g.name) || [];

      setData({
        id: data.id,
        title: data.title,
        artist: data.artist,
        cover: data.cover,
        cover_element: data.cover_element,
        album: data.album,
        genres: genre_list.join(", "),
        track_no: data.track_no,
        release_date: data.release_date,
        url: link
      });
    } catch (err) {
      console.error("Failed to retrieve data:", err);
    } finally {
      setProcess(false);
    }
  };

  useEffect(() => {
    if (!process) return;
    fetchData();
  }, [process]);


  const downloadMp3 = async() => {
    const response = await fetch('/api/download_mp3/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: data })

    });

    // Retrieve blob data from pytube on flask
    const blob = await response.blob();

    const arrayBuffer = await blob.arrayBuffer();

    const mp3tag = new MP3Tag(arrayBuffer);
    mp3tag.read();

    if (mp3tag.error) {
      alert("Read error:", mp3tag.error);
      return;
    }

    if (!Array.isArray(mp3tag.frames)) {
      mp3tag.frames = [];
    }

    const imageData = await fetchImage(data.cover);
    mp3tag.frames.push({
      id: 'APIC',
      value: {
        format: 'image/jpeg',
        type: 3,
        description: 'Cover',
        data: imageData
      }
    });


    // Set metadata
    mp3tag.tags.title = data.title;
    mp3tag.tags.artist = data.artist;
    mp3tag.tags.v2.TPE2 = data.artist;
    mp3tag.tags.album = data.album;
    mp3tag.tags.genre = data.genres;
    mp3tag.tags.track = (data.track_no);
    mp3tag.tags.year = data.release_date;

    mp3tag.save({
      id3v2: {
        include: true,
        version: 4
      }
    });

    // Download edited file
    const editedBlob = new Blob([mp3tag.buffer], { type: 'audio/mpeg' });
    const url = window.URL.createObjectURL(editedBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.title}`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  async function fetchImage(imageUrl) {
    const response = await fetch(imageUrl);
    const arrayBuffer = await response.arrayBuffer();
    return new Uint8Array(arrayBuffer);
  }

  const renderResult = () => {
    return Object.keys(data).length === 0 ? <div></div> : (
      <div className='w-100 h-110 border-2 rounded-2xl text-center flex flex-col justify-between items-center p-5'>
        <img src={data.cover_element} alt="cover"/>
        <h1 className='text-2xl font-bold'>{data.artist} - {data.title}</h1>
        <button type='button' className='duration-300 ease-in border-blue-600 border-2 rounded-sm text-blue-600 p-1 w-1/2 hover:cursor-pointer hover:bg-blue-600 hover:text-white hover:ease-out hover:duration-300' onClick={downloadMp3}>Download</button>
      </div>
    );
  }

  return (
    <div className='w-full h-screen p-10 flex flex-col justify-between items-center'>
      <h1 className='text-4xl font-extrabold'>YouTube to Mp3 Converter</h1>

      <div className='flex justify-between gap-5'>
        <input type="search" name="url" id="url" className='border-2 border-black p-3 w-150 h-10 rounded-md' onChange={(e)=> setLink(e.target.value)} placeholder='Enter a YouTube link'/>
        <input type="button" value="Search" className='duration-300 ease-in border-blue-600 border-2 rounded-sm text-blue-600 p-1 w-20 hover:cursor-pointer hover:bg-blue-600 hover:text-white hover:ease-out hover:duration-300' onClick={(e) => {
          setProcess(true);
        }}/>
      </div>
      
      {
        renderResult()
      }
    </div>
  )
}

export default App
