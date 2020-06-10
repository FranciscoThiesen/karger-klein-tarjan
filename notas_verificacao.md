# Notas sobre a verificação em O(n)

Vou seguir as notas do Hagerup, que a princípio tem o método mais simples para verificação de árvores.

Estou tentando entender melhor o processo de verificação. A princípio ele só é linear em árvores que são __full branching trees (FBT)__ (Todos os nós internos tem ao menos 2 filhos e todas as folhas da árvore estão na mesma altura).

A ideia do algoritmo de verificação é a seguinte:

1. Temos uma árvore geradora $T$ que queremos checar se é mínima
2. Seja $HeavyEdge(U, V)$ o custo da aresta mais pesada no caminho de $U \rightarrow V$ usando apenas arestas de $T$. 
3. Para isso, temos que garantir que para toda aresta $(U, V, W) \notin T$ vale que $W >= HeavyEdge(U, V)$. Caso contrário, poderiamos incluir essa aresta $(U, V, W)$ em T e estariamos diminuindo seu custo total.
4. Para que isso possa ser resolvido em tempo linear, é necessário verificar a condição mencionada acima para todas as arestas que não pertencem a $T$. Para fazer isso em tempo linear é necessário responder a query $HeavyEdge(x, y)$ em tempo constante.

Vou seguir a implementação descrita por esse paper (https://www.researchgate.net/publication/220752994_An_Even_Simpler_Linear-Time_Algorithm_for_Verifying_Minimum_Spanning_Trees) e vou resumir os passos tomados.

Passo 1 - Transformar a sua árvore geradora $T$ em uma _FBT_ $B$. Esse processo pode ser feito em tempo linear, utilizando uma adaptação do Boruvka. A ideia é que cada nó $x \in T$ vai passar a ser uma folha na nova árvore $B$. O processo está descrito em detalhes na seção 2 desse paper ([https://www.cs.princeton.edu/courses/archive/fall03/cs528/handouts/A%20Simpler%20Minimum%20Spanning.pdf](https://www.cs.princeton.edu/courses/archive/fall03/cs528/handouts/A Simpler Minimum Spanning.pdf))





