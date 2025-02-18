import * as vscode from "vscode";

interface FileMetadata {
    filePath: string;
    content: string;
}

export interface Window {
    code: string;
    metadata: {
        filePath: string;
        lineNo: number;
        startLineNo: number;
        endLineNo: number;
        windowSize: number;
        sliceSize: number;
    }
}

export interface CodeChunk {
    code: string;
    metadataList: any;
}

async function getWorkspaceFiles(): Promise<FileMetadata[]> {
    const filesMetadata: FileMetadata[] = [];

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage("No workspace folder is open.");
        return [];
    }
    const files = await vscode.workspace.findFiles("**/*");
    for (const file of files) {
        try {
            // @ts-ignore
            const fileContent = await vscode.workspace.fs.readFile(file);
            if (file.fsPath.endsWith(".py") || file.fsPath.endsWith(".java")) {
                const metadata: FileMetadata = {
                    filePath: file.fsPath,
                    content: Buffer.from(fileContent).toString("utf8")
                };
                filesMetadata.push(metadata);
            }
            if (file.fsPath.endsWith(".ipynb")) {
                const fileString = Buffer.from(fileContent).toString("utf8");
                const jsonContent = JSON.parse(fileString);
                const sourceCode: string[] = [];
                const cells = jsonContent.cells;
                for (const cell of cells) {
                    if (cell.cell_type == "code" && Array.isArray(cell.source)) {
                        sourceCode.push(cell.source.join(''));
                    }
                }
                const metadata: FileMetadata = {
                    filePath: file.fsPath,
                    content: sourceCode.join('\n')
                };
                filesMetadata.push(metadata);
            }
        } catch (err: any) {
            vscode.window.showErrorMessage(`Failed to read file ${file.fsPath}: ${err.message}`);
        }
    }
    return filesMetadata;
}

export class RepoWindowMaker {
    windowSize: number;
    sliceSize: number;
    sliceStep: number;
    sourceCodeFiles: FileMetadata[] = [];

    constructor(windowSize: number, sliceSize: number) {
        this.windowSize = windowSize;
        this.sliceSize = sliceSize;
        if (Math.floor(windowSize / sliceSize) == 0) {
            this.sliceStep = 1;
        } else {
            this.sliceStep = Math.floor(windowSize / sliceSize)
        }
    }
    async setSourceCodeFiles() {
        this.sourceCodeFiles = await getWorkspaceFiles();
    }

    buildWindowsForAFile(file: FileMetadata): Window[] {
        let windows = [];
        const codeLines = file.content.split('\n');
        const deltaSize = Math.floor(this.windowSize / 2);
        for (let lineNo = 0; lineNo < codeLines.length; lineNo += this.sliceStep) {
            const startLineNo = Math.max(0, lineNo - deltaSize);
            const endLineNo = Math.min(codeLines.length, lineNo + this.windowSize - deltaSize);
            const windowLines = codeLines.slice(startLineNo, endLineNo);
            if (!windowLines) {
                continue;
            }
            const windowText = windowLines.join('\n');
            windows.push({
                code: windowText,
                metadata: {
                    filePath: file.filePath,
                    lineNo: lineNo,
                    startLineNo: startLineNo,
                    endLineNo: endLineNo,
                    windowSize: this.windowSize,
                    sliceSize: this.sliceSize
                }
            });
        }
        return windows;
    }

    mergeWindowsWithSameContext(windows: Window[]): CodeChunk[] {
        let dict: {[key: string]: any} = {};
        for (const window of windows) {
            if (window.code in dict) {
                dict[window.code].push({...window.metadata});
            } else {
                dict[window.code] = [{...window.metadata}];
            }
        }
        let result: CodeChunk[] = [];
        for (const key in dict) {
            result.push({
                code: key,
                metadataList: dict[key]
            });
        }
        return result;
    }

    async buildWindows(): Promise<CodeChunk[]> {
        await this.setSourceCodeFiles();
        let windows: Window[] = [];
        for (const file of this.sourceCodeFiles) {
            const res = this.buildWindowsForAFile(file);
            windows = windows.concat(res);
        }
        return this.mergeWindowsWithSameContext(windows);
    }
}
