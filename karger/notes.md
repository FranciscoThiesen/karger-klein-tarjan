## Notas de estudo sobre o [Algoritmo](http://cs.brown.edu/research/pubs/pdfs/1995/Karger-1995-RLT.pdf)

### Preliminares

O trabalho assume que a árvore geradora mínima é única. Uma condição suficiente para que isso acontece é fazer com que todas as arestas tenham pesos distintos.

Isso pode ser alcançado em um grafo qualquer, ao introduzir um segundo componente de peso para cada aresta de modo a quebrar possíveis empates.



### Propriedades essenciais

__Propriedade de ciclo:__ Para qualquer ciclo $C$ no grafo, a aresta mais pesada $\in C$ não pertence a árvore geradora mínima/floresta geradora mínima.

__Propriedade do corte:__ Para qualquer subconjunto próprio, não-vazio $X$ de vértices, a aresta mais leve com exatamente uma extremidade em $X$ pertence a floresta/árvore geradora mínima.



### Lema de amostragem

O algoritmo é baseado em um passo de amostragem aleatória para descartar arestas que não podem estar contidas na árvore geradora mínima. A eficácia desse procedimento será demostrada por um lema mais adiante.

Seja $G$ um grafo com arestas que possuem pesos. Vamos denotar por $w(x, y)$ o peso da aresta $(x, y)$. Se $F$ é uma floresta em $G$, vamos denotar por $F(x, y)$ o caminho (se existir) conectando $x$ e $y$, e por $w_F(x, y)$ o peso da aresta mais cara em $F(x, y)$ e $W_f(x, y) = \infin$ se $x$ e $y$ não estiverem conectados em $F$. 

Vamos chamar uma aresta $(x, y)$ de _F-heavy_ se $w(x, y) > w_F(x,y)$ e _F-light_, caso contrário.

Dado uma floresta $F$ em $G$, as arestas _F-heavy_ de $G$ podem ser computadas em tempo linear no número de arestas de $G$, usando uma adaptação do algoritmo de verificação de _Dixon et al._



### Lema

Seja $H$ um subgrafo obtido incluindo cada aresta de $G$ com probabilidade $p$ e de forma independente, e seja $G$ a floresta geradora mínima de $H$. O número esperado de arestas _F-light_ $\in G$ é no máximo $\frac{n}{p}$, onde $n$ é o número de vértices de $G$.

### Prova do lema

Vou entrar nisso depois de ler mais sobre o algoritmo.



### O algoritmo

O algoritmo em si mescla passos do algoritmo de Boruvka, com passos de amostragem aleatória. Cada passo Boruvka reduz a quantidade de vértices por um fator de pelo menos 2; cada passo de amostragem aleatória descarta arestas o suficiente para reduzir a densidade para uma constante fixa com alta probabilidade.

A ideia é recursiva. Geramos dois subproblemas, mas, com alta probabilidade o tamanho total desses subproblemas é no máximo uma fração constante do problema inicial -1. Esse fato é a base para a garantia de uma complexidade que é probabilisticamente linear.

Vamos começar descrevendo o passo Boruvka.

__Passo Boruvka:__ Para cada vértice, seleciona a aresta incidente nele de peso mínimo. Depois, todas as arestas selecionadas são contraídas, de forma a substituir cada componente conexa resultante com um único vértice e deletando todos os vértices isolados, loops (arestas que vão que tem ambas extremidades no mesmo super-vértice) e todas arestas entre duas super-componentes que não são mínimas. Esse passo garantidamente reduz a quantidade de vértices por 2.



Algoritmo

Enquanto o grafo não for vazio:

​	1 - Aplique dois passos Boruvkas sucessivos. Isso reduz a quantidade de vértices por um fator de 4.

​	2 - No grafo contraído, escolha um subgrafo $H$ que contém cada aresta com probabilidade independente de $\frac{1}{2}$. Aplique o algoritmo de forma recursiva em $H$, produzindo uma floresta geradora mínima $F$ de $H$. Encontra todas as arestas _F-heavy _ (Testar as arestas que estão em H e não estão) e delete elas do grafo contraído.

​	3 - Aplique o algoritmo de forma recursiva no grafo restante para computar a floresta geradora mínima $F'$. Retorne as arestas contraídas no passo 1 juntamente com as arestas de $F'$ 





   









