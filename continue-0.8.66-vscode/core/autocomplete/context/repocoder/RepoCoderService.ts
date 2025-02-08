import { encode } from "gpt-tokenizer";
import { RepoWindowMaker, Window, CodeChunk } from "./parseProject";
import { Position } from "../../..";
import {
    AutocompleteCodeSnippet,
    AutocompleteSnippetType,
} from "../../snippets/types";
import { IDE } from "../../..";


export class RepoCoderService {
    windowSize = 20;
    sliceSize = 2;
    repoWindowMaker: RepoWindowMaker;

    constructor(private readonly ide: IDE) {
        this.repoWindowMaker = new RepoWindowMaker(this.windowSize, this.sliceSize);
    }

    jaccard_similarity(list1: number[], list2: number[]): number {
        const set1 = new Set<number>(list1);
        const set2 = new Set<number>(list2);
        const union = new Set<number>([...set1, ...set2]);
        const intersection = new Set<number>([...set1].filter(x => set2.has(x)));
        return intersection.size / union.size;
    }

    async retrieve(cursor: Position, fileLines: string[], currentFilePath: string, topK: number): Promise<AutocompleteCodeSnippet[]> {
        const cursorLine = cursor.line;
        const startLineNo = Math.max(0, cursorLine - Math.floor(this.windowSize / 2));
        const windowLines = fileLines.slice(startLineNo, cursorLine)
        const queryWindow: Window = {
            code: windowLines.join("\n"),
            metadata: {
                filePath: currentFilePath,
                lineNo: cursorLine,
                startLineNo: startLineNo,
                endLineNo: cursorLine,
                windowSize: this.windowSize,
                sliceSize: this.sliceSize
            }
        }
        const workspaceCodeChunks: CodeChunk[] = await this.repoWindowMaker.buildWindows();
        let topKCodeChunks = [];
        for (const codeChunk of workspaceCodeChunks) {
            const simScore = this.jaccard_similarity(encode(queryWindow.code), encode(codeChunk.code));
            topKCodeChunks.push({simScore: simScore, codeChunk: codeChunk})
        }
        topKCodeChunks = topKCodeChunks.sort((a, b) => b.simScore - a.simScore);
        topKCodeChunks = topKCodeChunks.slice(0, topK);
        const codeSnippets = await Promise.all(
            topKCodeChunks.map(async (codeChunk,_) => {
                const rightAfterCodeChunk = await this.makeAnExtendedBlock(codeChunk);
                return {
                    content: rightAfterCodeChunk.code,
                    filepath: rightAfterCodeChunk.metadataList[0].filePath,
                    type: AutocompleteSnippetType.Code
                } as AutocompleteCodeSnippet;
            })
        );

        return codeSnippets;
    }

    async makeAnExtendedBlock(retrievedCodeChunk: any): Promise<CodeChunk> {
        const { simScore, codeChunk } = retrievedCodeChunk;
        const metadata = codeChunk.metadataList;
        const {filePath, endLineNo, windowSize, sliceSize, lineNo } = metadata[0]
        const fileContent = await this.ide.readFile(filePath);
        const fileLines = fileContent.split(/\r?\n/);
        const newEndLineNo = Math.min(endLineNo + Math.floor(windowSize / sliceSize), fileLines.length);
        const newStartLineNo = Math.max(0, newEndLineNo - windowSize);
        const contentLines = fileLines.slice(newStartLineNo, newEndLineNo);
        const code = contentLines.join("\n");
        const newMetadata = {
            filePath: filePath,
            lineNo: Math.min(lineNo + Math.floor(windowSize / sliceSize), fileLines.length),
            startLineNo: newStartLineNo,
            endLineNo: newEndLineNo,
            windowSize: windowSize,
            sliceSize: sliceSize
        }
        return {
            code: code,
            metadataList: [newMetadata]
        }
    }

}
