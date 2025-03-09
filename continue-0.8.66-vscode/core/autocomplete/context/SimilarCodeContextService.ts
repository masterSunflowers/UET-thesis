
import { Position } from "../..";
import {
    AutocompleteCodeSnippet,
    AutocompleteSnippetType,
} from "../snippets/types";
import { IDE } from "../..";
import { LlamaAsyncEncoder } from "../../llm/asyncEncoder";
import { SqliteDb, DatabaseConnection } from "../../indexing/refreshIndex";
import { jaccardSimilarity } from "./ranking";

export class SimilarCodeContextService {
    // I hashcode here for the early development stage, 128 is the max chunk size when Continue indexing (chunking code) for default
    private maxChunkSize = 128;
    // I hashcode here for the early development stage, get top 10 similar code snippets
    private topK = 10;
    private llamaTokenizer = new LlamaAsyncEncoder();

    constructor(private ide: IDE) {
        this.ide = ide;
    }

    async buildRetrieveQuery(cursor: Position, fileLines: string[]): Promise<string> {
        // Recursive extend to two sides to reach `maxChunkSize`
        let startLineNo = cursor.line;
        let endLineNo = cursor.line + 1;
        let queryText = "";
        while (startLineNo >= 0 && endLineNo <= fileLines.length) {
            queryText = fileLines.slice(startLineNo, endLineNo).join("\n");
            const encodedQueryText = await this.llamaTokenizer.encode(queryText);
            if (encodedQueryText.length > this.maxChunkSize) {
                break;
            }
            startLineNo--;
            endLineNo++;
        }
        queryText = fileLines.slice(startLineNo + 1, endLineNo - 1).join("\n");
        while (true) {
            const encodedQueryText = await this.llamaTokenizer.encode(queryText);
            if (encodedQueryText.length >= this.maxChunkSize || startLineNo < 0) break;
            queryText = fileLines[startLineNo] + "\n" + queryText;
            startLineNo--;
        }
        while (true) {
            const encodedQueryText = await this.llamaTokenizer.encode(queryText);
            if (encodedQueryText.length >= this.maxChunkSize || endLineNo >= fileLines.length) break;
            queryText = queryText + "\n" + fileLines[endLineNo];
            endLineNo++;
        }
        return queryText;
    }

    async retrieve(cursor: Position, fileLines: string[]): Promise<AutocompleteCodeSnippet[]> {  
        try {
            const queryText = await this.buildRetrieveQuery(cursor, fileLines);
            const encodedQueryText = await this.llamaTokenizer.encode(queryText);
            const candidateSnippets = await this.query();
            const encodedCandidateSnippets = await Promise.all(candidateSnippets.map(async (snippet: any) => {
                const encodedSnippet = await this.llamaTokenizer.encode(snippet.content);
                const similarity = jaccardSimilarity(encodedQueryText, encodedSnippet);
                return { ...snippet, encodedSnippet, similarity };
            }));
            
            const ranking = encodedCandidateSnippets.sort((a: any, b: any) => b.similarity - a.similarity);
            let result: AutocompleteCodeSnippet[] = [];
            for (let i = 0; i < Math.min(ranking.length, this.topK); i++) {
                result.push({
                    filepath: ranking[i].path,
                    content: ranking[i].content,
                    type: AutocompleteSnippetType.Code,
                });
            }
            return result;
        } catch (error) {
            console.error("Error in similar code retrieval:", error);
            return [];
        }

    }

    async query(): Promise<any> {
        const db: DatabaseConnection = await SqliteDb.get();
        const workspaceDirs = await this.ide.getWorkspaceDirs();
        const workspaceDir = workspaceDirs[0];
        const query = `SELECT path, startLine, endLine, content FROM chunks WHERE INSTR(path, ?) > 0`;
        const params = [workspaceDir];
        const result = await db.all(query, params);
        return result;
    }
     
}