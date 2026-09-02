#ifndef COMPANION_TREE_INFER_H
#define COMPANION_TREE_INFER_H

#include <stdint.h>

typedef struct {
  int8_t f;
  float t;
  int16_t l;
  int16_t r;
  float v;
} companion_tree_node_t;

static inline float companion_tree_infer(const companion_tree_node_t *nodes, int n_nodes, const float *x, int n_feat) {
  int i = 0;
  int guard = 0;
  while (guard++ < n_nodes) {
    const companion_tree_node_t *n = &nodes[i];
    if (n->f < 0) {
      float v = n->v;
      if (v < 0) v = 0;
      if (v > 1) v = 1;
      return v;
    }
    float val = 0;
    if (n->f < n_feat) val = x[n->f];
    i = (val <= n->t) ? n->l : n->r;
    if (i < 0 || i >= n_nodes) return 0;
  }
  return 0;
}

#endif
