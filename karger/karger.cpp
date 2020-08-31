// Esboco inicial da implementação...


// Essa função vai aplicar o passo Boruvka, descrito no paper do KKT. A ideia é diminuir 
// a quantidade de vértices pela metade, ainda em tempo linear.

// Se eu quiser retornar as arestas utilizadas, preciso pensar em manter para cada nó, qual super-nó ele pertence..
// Mesmo que as extremidades das arestas mudem ao longo do tempo, posso manter um índice que permite que cada aresta
// da MST seja mapeada para alguma das arestas originais.
vector< tuple<int, int, int> > boruvka_step(const vector< tuple<int, int, int> >& G) {
    // implementar!
    // Aqui, preciso retornar o grafo resultante e também as arestas que foram utilizadas!
}

// Seleciona arestas de G com probabilidade = 1/2. Esse processo é descrito no paper do KKT,
// onde essa etapa é chamada de Random Sampling.
vector< tuple<int, int, int> > random_sampling(const vector< tuple<int, int, int> >& G) {
    vector< tuple<int, int, int> > H;
    for(const auto& E : G) {
        int b = (rand() & 1);
        if(b) H.push_back(E);
    }
    return H;
}

// Retorna o custo da minimum-spanning-tree, em tempo esperado linear.
// Seguindo o processo descrito pelo paper KKT.
vector< tuple<int, int, int> > kkt(const vector< tuple<int, int, int> >& G) {
    vector< tuple<int, int, int> > resp;
    if(G.empty()) return resp;
}
