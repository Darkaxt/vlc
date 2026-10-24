// SPDX-License-Identifier: GPL-2.0-or-later
// Native regression for the pinned Qt/MinGW animation-timer teardown.
#include <QCoreApplication>
#include <QThread>
#include <QRegularExpression>
#include <QtCore/private/qabstractanimation_p.h>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <malloc.h>
#include <windows.h>

static void *timers[2];
static std::atomic<unsigned> destroyed{0};
struct pcre2_real_jit_stack_16;
struct pcre2_real_general_context_16;
using JitStack = pcre2_real_jit_stack_16;
using JitContext = pcre2_real_general_context_16;
static std::atomic<JitStack *> jitStack{nullptr};
static std::atomic<bool> jitDestroyed{false};
extern "C" JitStack *__real_pcre2_jit_stack_create_16(size_t, size_t, JitContext *);
extern "C" void __real_pcre2_jit_stack_free_16(JitStack *);
extern "C" JitStack *__wrap_pcre2_jit_stack_create_16(size_t start, size_t max, JitContext *context)
{
    auto *stack = __real_pcre2_jit_stack_create_16(start, max, context);
    jitStack = stack;
    return stack;
}
extern "C" void __wrap_pcre2_jit_stack_free_16(JitStack *stack)
{
    if (stack == jitStack) jitDestroyed = true;
    __real_pcre2_jit_stack_free_16(stack);
}
extern "C" void __real_free(void *);
extern "C" void __wrap_free(void *pointer)
{
    // GCC emutls allocations have their allocation base immediately before
    // the aligned object. Observe that exact identity; do not poison memory
    // or alter allocator/destructor ordering to manufacture the regression.
    if (pointer && _msize(pointer) >= 2 * sizeof(void *))
    {
        auto **words = static_cast<void **>(pointer);
        const bool timerOwner = (words[1] == timers[0] || words[1] == timers[1]) && destroyed.load() != 2;
        const bool jitOwner = words[1] == jitStack && !jitDestroyed;
        if (words[0] == pointer && words[1] && (timerOwner || jitOwner))
        {
            std::fputs(timerOwner ? "FAIL: emutls frees an animation-timer owner before its destructor\n"
                                 : "FAIL: emutls frees a regex JIT owner before its destructor\n", stderr);
            std::fflush(stderr);
            // This callback runs under the Windows loader lock. ExitProcess
            // would re-enter DLL teardown; end this failed regression directly.
            TerminateProcess(GetCurrentProcess(), 23);
        }
    }
    __real_free(pointer);
}

class Worker final : public QThread
{
    void run() override
    {
        timers[0] = QUnifiedTimer::instance();
        timers[1] = QAnimationTimer::instance();
        for (auto *timer : timers)
            QObject::connect(static_cast<QObject *>(timer), &QObject::destroyed,
                             [](QObject *) { ::destroyed.fetch_add(1); });
        // Qt's existing pcreJitStackUsage regression requests an expanded
        // real JIT stack, exercising the other nontrivial QtBase TLS owner.
        QRegularExpression expression(QStringLiteral("(?(R)a*(?1)|((?R))b)"));
        expression.match(QStringLiteral("aaaabcde"));
    }
};
int main(int argc, char **argv)
{
    _set_error_mode(_OUT_TO_STDERR);
    QCoreApplication app(argc, argv);
    qputenv("QT_ENABLE_REGEXP_JIT", "1");
    Worker worker;
    worker.start();
    worker.wait();
    if (destroyed != 2 || !jitStack || !jitDestroyed) return 24;
    std::puts("PASS: animation timers and regex JIT stack are destroyed before thread storage release");
}
