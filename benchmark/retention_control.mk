# Separate targets; the existing Makefile and five-solver harness are frozen.
# Invoke from the repository root with native compiler/macro flags explicitly.
include Makefile

RETENTION_DEPS = benchmark/retention_control.cpp benchmark/retention_boruvka.hpp kkt/experimental_multigraph_contraction.hpp $(MST_SEARCH_DEPS)

.PHONY: retention-control retention-control-test
retention-control: $(BIN_DIR)/retention_control
retention-control-test: $(BIN_DIR)/retention_control_test

$(BIN_DIR)/retention_control: $(RETENTION_DEPS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. benchmark/retention_control.cpp $(OBJS) $(LDFLAGS) -Wl,-stack_size,0x20000000 -o $@

$(BIN_DIR)/retention_control_test: test/retention_control_test.cpp $(RETENTION_DEPS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. test/retention_control_test.cpp $(OBJS) $(LDFLAGS) -Wl,-stack_size,0x20000000 -o $@
