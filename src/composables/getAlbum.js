let base_uri = "http://127.0.0.1:9876";

const getAlbum = async (name) => {
  const res = await fetch(base_uri + "/albums/" + name);

  if (!res.ok) {
    const message = `An error has occured: ${res.status}`;
    throw new Error(message);
  }

  const data = await res.json();

  return data;
};

export default getAlbum;