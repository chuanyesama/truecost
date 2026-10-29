// Runs TrueCost's Python engine (app/web.py + src/) in the browser with Pyodide, off the main thread.
// The statement is analysed here, inside the viewer's browser; it is never sent anywhere.
// Messages in:  {id, fn, args} -> web.call(fn, args).  Messages out: {id, result} / {id, error} / {progress}.
const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.27.2/full/";
const ENGINE_VERSION = "c39de0ec52";  // set by scripts/build_web.py

importScripts(PYODIDE + "pyodide.js");

const say = (step) => postMessage({ progress: step });

const ready = (async () => {
  say("python");
  const py = await loadPyodide({ indexURL: PYODIDE });
  say("packages");
  const engine = fetch("engine.zip?v=" + ENGINE_VERSION).then(r => {
    if (!r.ok) throw new Error("engine.zip " + r.status);
    return r.arrayBuffer();
  });
  await py.loadPackage(["pandas", "tzdata"]);
  say("engine");
  py.unpackArchive(await engine, "zip", { extractDir: "/truecost" });
  py.runPython("import sys; sys.path[:0] = ['/truecost', '/truecost/app']; import web");
  say("ready");
  return { py, call: py.globals.get("web").call };
})();

onmessage = async (e) => {
  const { id, fn, args, file } = e.data;
  try {
    const { py, call } = await ready;
    if (file) py.FS.writeFile(args.path, new Uint8Array(file));  // read and deleted by web.load_file
    postMessage({ id, result: call(fn, JSON.stringify(args || {})) });
  } catch (err) {
    postMessage({ id, error: String(err && err.message || err) });
  }
};
