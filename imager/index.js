import puppeteer from "puppeteer";
import path from "path"
import fsp from "fs/promises"
import { exit } from "process";



async function* getFiles (dir) {
    const dirents = await fsp.readdir(dir, { withFileTypes: true });
    for (const dirent of dirents) {
        const res = path.resolve(dir, dirent.name);
        if (dirent.isDirectory()) {
            yield* getFiles(res);
        } else {
            yield res;
        }
    }
}


const test = async (gen) => {
    let paths = []
    for await (const f of getFiles('../out')) {
        if(path.extname(f) == "html") {
            paths.push({ "path": f, "pdf": "KW_" + path.basename(f).replace(path.extname(f),"") + ".pdf"});
        }
    }
    for (let index = 0; index < paths.length; index++) {
        const element = paths[index];
        console.log(element);
    }
}

const main = async ()=> {
    const browser = await puppeteer.launch({headless: "new"})
    const page = await browser.newPage();
    let paths = []
    for await (const f of getFiles('out')) {
        if(path.extname(f) == ".html") {
            paths.push({ "path": f, "pdf": "KW_" + path.basename(f).replace(path.extname(f),"") + ".pdf"});
        }
    }
    for (let index = 0; index < paths.length; index++) {
        const element = paths[index];
        await page.goto("file://" + element.path);
        await page.pdf({
            path: 'out/pdf/' +  element.pdf,
            scale: 1,
            margin: { top: '3cm', right: '3cm', bottom: '0px', left: '3cm' },
            format: 'A4',
        });
    }
    await browser.close()
}

main()