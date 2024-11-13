import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { toast } from "@/components/hooks/use-toast"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"

const FormSchema = z.object({
  fullName: z.string().min(2, {
    message: "Full name must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Invalid email address.",
  }),
  company: z.string().min(2, {
    message: "Company name must be at least 2 characters.",
  }),
  country: z.string().min(2, {
    message: "Country name must be at least 2 characters.",
  }),
  phone: z.string().min(2, {
    message: "Phone number must be at least 2 characters.",
  }),
})

export function InputForm() {
  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      fullName: "",
      email: "",
      company: "",
      country: "",
      phone: "",
    },
  })

  // Get all field names for checking errors
  const fieldNames = ['fullName', 'email', 'company', 'country', 'phone'] as const

  // Find the first field with an error
  const firstErrorField = fieldNames.find(
    fieldName => form.formState.errors[fieldName]
  )

  function onSubmit(data: z.infer<typeof FormSchema>) {
    toast({
      title: "You submitted the following values:",
      description: (
        <pre className="mt-2 w-[340px] rounded-md bg-slate-950 p-4">
          <code className="text-white">{JSON.stringify(data, null, 2)}</code>
        </pre>
      ),
    })
  }

  // Helper function to determine if error should be shown for a field
  const shouldShowError = (fieldName: string) => {
    return firstErrorField === fieldName
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col h-full">
        <div className="flex-grow space-y-4">
          <FormField
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Full Name</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                {shouldShowError('username') && <FormMessage />}
              </FormItem>
            )}
          />
          <FormField
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                {shouldShowError('email') && <FormMessage />}
              </FormItem>
            )}
          />
          <FormField
            name="company"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Company</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                {shouldShowError('company') && <FormMessage />}
              </FormItem>
            )}
          />
          <FormField
            name="country"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Country</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                {shouldShowError('country') && <FormMessage />}
              </FormItem>
            )}
          />
          <FormField
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Phone</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                {shouldShowError('phone') && <FormMessage />}
              </FormItem>
            )}
          />
        </div>

        <Button type="submit" className="w-full rounded-xl mt-8" variant={'default'}>
          Submit
        </Button>
      </form>
    </Form>
  )
}

function App() {
  return (
    <div className="h-screen w-screen bg-gray-300">
      <div className="flex flex-col justify-center items-center h-full w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Data Security Assessment Tool
          </h1>
          <p className="text-lg text-gray-700">
            Comprehensive data security assessment tool for your business.
          </p>
        </div>
        <div className="bg-white p-8 rounded-lg shadow-lg w-[600px] h-[600px] rounded-xl flex flex-col">
          <InputForm />
        </div>

        <p className="text-gray-700 text-sm">
          © Powered by Ray Security
        </p>
      </div>
    </div>
  )
}

export default App