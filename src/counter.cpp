// Token-boundary substring counter.
//
// stdin:  line 1 = path of one log file, line 2 = query string (< 100 chars)
// stdout: number of occurrences of the query whose left AND right neighbours
//         are both delimiters (or line start / end); -1 if the file can't be opened.

#include <cstdio>
#include <cstring>

static char buf[1000000];

int main() {

    bool delim[256];
    memset(delim, 0, sizeof(delim));
    delim['\0'] = true;
    delim[' '] = true;
    delim['\t'] = true;
    delim[':'] = true;
    delim['='] = true;
    delim[','] = true;
    delim['['] = true;
    delim[']'] = true;


    char LogPath[4096];
    if(fgets(LogPath, sizeof(LogPath), stdin) == NULL) {
        printf("-1\n");
        return 0;
    }
    int pathlen = strlen(LogPath);
    if(pathlen > 0 && LogPath[pathlen - 1] == '\n') LogPath[pathlen - 1] = '\0';


    char Query[100];
    if(fgets(Query, sizeof(Query), stdin) == NULL) {
        printf("0\n");
        return 0;
    }
    int ql = strlen(Query);
    if(ql > 0 && Query[ql - 1] == '\n') Query[ql - 1] = '\0', ql--;
    if(ql == 0) {
        printf("0\n");
        return 0;
    }


    FILE *fp = fopen(LogPath, "r");
    if(fp == NULL) {
        printf("-1\n");
        return 0;
    }
    long long count = 0;
    while(fgets(buf, sizeof(buf), fp)) {
        int bl = strlen(buf);
        if(bl > 0 && buf[bl - 1] == '\n') {
            buf[bl - 1] = '\0';
            bl --;
        }

        for(int i = 0; i + ql <= bl; i++) {
            if(i > 0) {
                if(delim[(unsigned char)buf[i-1]] == false) continue;
            }
            if(i + ql < bl) {
                if(delim[(unsigned char)buf[i+ql]] == false) continue;
            }

            bool tag = true;
            for(int j = 0; j < ql; j++) {
                if(Query[j] != buf[i+j]) { tag = false; break; }
            }
            if(tag) count ++;
        }
    }

    fclose(fp);
    printf("%lld\n", count);

    return 0;
}
