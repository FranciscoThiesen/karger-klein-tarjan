#!/usr/bin/env python3
"""Archive disassembly of the actual paired objects; do not infer inlining from flags."""
import argparse
import importlib.util
from pathlib import Path
import signal

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('depth_codegen_candidate', HERE/'run_candidate.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
base = candidate.base


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--build', required=True, type=Path)
    args = parser.parse_args()
    output, build_path = args.output.resolve(), args.build.resolve()
    output.mkdir(parents=True, exist_ok=False)
    status = {'validation': 'running', 'commands': []}
    bound = {}
    try:
        build, bound = candidate.check_build(build_path)
        objdump = Path('/opt/homebrew/opt/llvm/bin/llvm-objdump')
        candidate.add(bound, objdump)
        candidate.add(bound, Path(__file__))
        for policy in ('reference', 'depth', 'depth_noinline'):
            name = policy+'-reference'
            obj = build_path.parent/name/'verifier_v2.o'
            command = ['/usr/bin/arch', '-arm64', str(objdump), '-dr', '--demangle', str(obj)]
            base.recheck(bound)
            receipt = base.run_owned(command, output, name, timeout=30)
            status['commands'].append(receipt)
            for suffix, digest in (('.json', None), ('.stdout', receipt['stdout_sha256']),
                                   ('.stderr', receipt['stderr_sha256'])):
                candidate.add(bound, output/(name+suffix), digest)
        base.recheck(bound)
        status['validation'] = 'pass'
    except BaseException as error:
        status.update(validation='failed', error=repr(error))
        raise
    finally:
        status.update(bound_sha256=bound, native_process_may_still_be_running=base._launch_blocked)
        base.write(output/'inspection.json', status)


if __name__ == '__main__':
    def stopped(signum, frame):
        raise KeyboardInterrupt('code inspection received SIGTERM')
    signal.signal(signal.SIGTERM, stopped)
    main()
