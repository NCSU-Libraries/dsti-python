// Scenes for tools/record-tour.mjs: the Mac flow of the Setup page, step by step.
// Commands match site/setup.qmd character for character. The words in the terminal are what uv and JupyterLab print,
// shortened to fit: uv 0.13.3 is the version the Setup page was checked with, CPython 3.13.16 is what it downloads
// today, and the package counts and the JupyterLab, matplotlib and Jupyter Server versions come from a real
// `uv add jupyterlab matplotlib` run. The Setup page in the browser frame is the real page. The JupyterLab frames are
// real screenshots of JupyterLab 4.6.4 in headless Chrome, captured with tools/shoot.mjs from a scratch
// `uv init --python 3.13 --vcs none dss-python` project (made with uv 0.9.10, which makes an app without a package, so
// the file list matches `--no-package`: main.py, pyproject.toml, README.md, uv.lock), in five states:
//   jlab-a  the new project's file list, no notebook        jlab-d0  scrolled to "Example: a simple bar plot"
//   jlab-b  the notebook is in the file list                jlab-d   the bar plot cell selected (a real click)
//   jlab-c  the notebook open at the top                    jlab-e   after a real Shift+Enter: the bar chart
const NOTEBOOK = 'introduction-to-programming-with-python.ipynb';

export default ({ S, js, sleep, moveTo, hoverText, click }) => {
  const cap = (t) => S(`stage.caption(${js(t)})`);
  const step = (t) => S(`stage.step(${js(t)})`);
  const layout = (l) => S(`stage.layout(${js(l)})`);
  const cursor = (on) => S(`document.body.classList.toggle('carded', ${!on})`);
  const page = (file, label, zoom, jump = null) => S(`await stage.browser.load(${js('pages/' + file)}, ${js(label)}, ${zoom}, ${js(jump)})`);
  const show = (key, ms = 250) => S(`stage.browser.show(${js(key)}, ${ms})`);
  const lines = (items, gap = 420) => S(`await stage.term.lines(${js(items)}, ${gap})`);
  // A shell session: ready() adds a prompt, run() types a command into it and presses Enter.
  const ready = (cwd = '~') => S(`stage.term.prompt(${js(cwd)})`);
  const run = async (text, delay = 34) => {
    await sleep(500);
    await S(`await stage.term.type(${js(text)}, ${delay})`);
    await sleep(380);
    await S('stage.term.enter()');
    await sleep(250);
  };
  // Stage position of a point in a 1280x800 JupyterLab screenshot shown in the jlab layout (frame at 168,30; bar 30; zoom 0.7375).
  const jl = (x, y) => [168 + x * 0.7375, 60 + y * 0.7375];

  return [
    ['intro', async () => {
      await cursor(false);
      await S(`stage.card('Set up Python', 'uv, a project folder and JupyterLab, on your own laptop', { points: ['Install', 'Project', 'JupyterLab', 'Notebook'], instant: true })`);
      await sleep(3800);
      await S('stage.card(null)');
      await sleep(700);
    }],

    ['install', async () => {
      await step('2 · Install uv');
      await S(`stage.term.title('Terminal')`);
      await ready('~');
      await cap('Install uv with one line');
      await run('curl -LsSf https://astral.sh/uv/install.sh | sh');
      await lines([
        ['out', 'downloading uv 0.13.3 aarch64-apple-darwin'],
        ['out', 'installing to /Users/you/.local/bin'],
        ['out', '  uv'],
        ['out', '  uvx'],
        ['ok', 'everything\'s installed!'],
      ], 450);
      await ready('~');
      await sleep(900);
      await cap('On Windows, use PowerShell and the Windows line on the Setup page');
      await sleep(3600);
      await step('3 · Check it worked');
      await cap('Close the terminal, open a new one, then check');
      await sleep(2200);
      await S('await stage.term.reset()');
      await ready('~');
      await run('uv --version');
      await lines([['out', 'uv 0.13.3']], 300);
      await ready('~');
      await sleep(2000);
    }],

    ['project', async () => {
      await step('4 · Make your project folder');
      await cap(null);
      await run('uv init --python 3.13 --vcs none --no-package dss-python');
      await lines([['out', 'Initialized project `dss-python` at `/Users/you/dss-python`']], 500);
      await ready('~');
      await run('cd dss-python');
      await ready('dss-python');
      await cap('A folder with its own Python');
      await sleep(3200);
    }],

    ['add', async () => {
      await step('5 · Add JupyterLab and matplotlib');
      await cap(null);
      await run('uv add jupyterlab matplotlib');
      await lines([
        ['out', 'Using CPython 3.13.16'],
        ['out', 'Creating virtual environment at: .venv'],
        ['out', 'Resolved 102 packages in 1.8s'],
        ['dim prog', 'Preparing packages... (23/99)'],
      ], 450);
      await cap('The slow step: download the notebook while it runs');
      await sleep(3000);
      // To the real Setup page: scroll to "6. Download the notebook" and click the learner notebook.
      await step('6 · Download the notebook');
      await layout('browser');
      await sleep(800);
      // Open on step 5's heading, then glide down to step 6.
      await page('setup/index.html', 'ncsu-libraries.github.io/dsti-python/setup.html', 0.9, '[data-anchor-id="add-jupyterlab-and-matplotlib"]');
      await cursor(true);
      await sleep(700);
      await S(`await stage.browser.scrollTo('#notebook', 120, 1800)`);
      await sleep(600);
      if (!(await hoverText('Download the learner notebook', 1100))) throw new Error('learner notebook link not found');
      await sleep(600);
      await click();
      await sleep(250);
      await S(`stage.download(${js(NOTEBOOK)})`);
      await sleep(3200);
      await S('stage.download(null)');
      await sleep(400);
      // Back in the terminal, uv has finished.
      await cursor(false);
      await step('5 · Add JupyterLab and matplotlib');
      await layout('term');
      await sleep(1100);
      await S(`const p = document.querySelector('#lines .prog'); p.className = 'ln out'; p.textContent = 'Prepared 99 packages in 9.1s'`);
      await lines([
        ['out', 'Installed 99 packages in 397ms'],
        ['add', ' <b>+</b> jupyterlab==4.6.4'],
        ['add', ' <b>+</b> matplotlib==3.11.2'],
        ['add', ' <b>+</b> …'],
      ], 450);
      await ready('dss-python');
      await sleep(1800);
    }],

    ['open', async () => {
      await step('7 · Start JupyterLab');
      await cap(null);
      await run('uv run jupyter lab');
      await lines([
        ['out', '[I 2026-10-20 09:12:07.412 ServerApp] Jupyter Server 2.21.1 is running at:'],
        ['out', '[I 2026-10-20 09:12:07.412 ServerApp]     http://localhost:8888/lab?token=…'],
      ], 600);
      await cap('Leave this terminal open');
      await sleep(3800);
    }],

    ['jlab-files', async () => {
      await layout('jlab');
      await sleep(500);
      await page('jlab.html', 'localhost:8888/lab', 0.7375);
      await cursor(true);
      await cap('Your project folder: no notebook yet');
      await sleep(3200);
    }],

    ['jlab-drag', async () => {
      await cap('Drag the notebook from Downloads onto the file list');
      await S(`stage.dock(true, ${js(NOTEBOOK)})`);
      await sleep(1600);
      await moveTo(640, 476, 1000);
      await sleep(300);
      await S('stage.grab()');
      await sleep(250);
      await moveTo(...jl(160, 430), 1600);
      await sleep(400);
      await S('stage.drop()');
      await show('b', 200);
      await S('stage.dock(false)');
      await sleep(2800);
    }],

    ['jlab-open', async () => {
      await cap('Double-click the notebook to open it');
      await moveTo(...jl(125, 140), 1100);
      await sleep(500);
      await click(2);
      await show('c', 300);
      await sleep(3400);
    }],

    ['jlab-run', async () => {
      await cap('Scroll to Example: a simple bar plot');
      await show('d0', 700);
      await sleep(2000);
      await cap('Click the bar plot cell, then press Shift + Enter');
      await moveTo(...jl(640, 222), 1100);
      await sleep(400);
      await click();
      await show('d', 150);
      await S('stage.keys(true)');
      await sleep(2800);
      await S('stage.press(true)');
      await sleep(350);
      await S('stage.press(false)');
      await sleep(150);
      await show('e', 300);
      await S('stage.keys(false)');
      await sleep(500);
      await cap('A chart means everything works: Python, JupyterLab and matplotlib');
      await sleep(4800);
    }],

    ['colab', async () => {
      await S('stage.caption(null); stage.step(null)');
      await cursor(false);
      await S(`stage.card('Stuck? Colab is the backup', 'Same notebook, in your browser: Setup, step 10')`);
      await sleep(4500);
    }],

    ['outro', async () => {
      await S(`stage.card('Next time', null, { points: ['cd dss-python', 'uv run jupyter lab'], mono: true, url: 'go.ncsu.edu/dsti-python' })`);
      await sleep(5500);
    }],
  ];
};
