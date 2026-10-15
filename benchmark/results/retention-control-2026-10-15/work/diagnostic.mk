# Supplementary diagnostics only. Frozen Makefile/native recipes stay unchanged.
include Makefile

.PHONY: retention-work
retention-work: $(BIN_DIR)/retention_work

$(BIN_DIR)/retention_work: benchmark/results/retention-control-2026-10-15/work/driver.cpp $(HDRS) $(OBJS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $< $(OBJS) $(LDFLAGS) -Wl,-stack_size,0x20000000 -o $@
